from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import secrets

from core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_active_user
)
from db.session import get_db
from db.models.user import User
from db.models.organisation import Organisation
from db.models.company import Company

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=[" authentication"])

# Models
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    role: str = "company"
    organisation_name: Optional[str] = None
    organisation_id: Optional[int] = None
    company_name: Optional[str] = None

    @field_validator('organisation_name', 'company_name', mode='before')
    @classmethod
    def empty_string_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator('organisation_id', mode='before')
    @classmethod
    def coerce_organisation_id(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return v

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

class UserProfile(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str
    company_id: Optional[int] = None
    organisation_id: Optional[int] = None

@router.get("/organisations")
async def get_active_organisations(db: AsyncSession = Depends(get_db)):
    """Get list of active organisations for company registration"""
    try:
        result = await db.execute(
            select(Organisation)
            .where(Organisation.status == "active")
            .order_by(Organisation.name)
        )
        organisations = result.scalars().all()
        
        org_list = []
        for org in organisations:
            org_list.append({
                "id": org.id,
                "name": org.name,
                "email": org.email
            })
        
        return {
            "organisations": org_list,
            "total": len(org_list)
        }
    except Exception as e:
        logger.error(f"Error fetching organisations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch organisations")

@router.post("/register", response_model=dict)
async def register(user: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(
        (User.username == user.username) | (User.email == user.email)
    ))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(status_code=400, detail="Username already registered")
        else:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role,
        status="active"
    )
    db.add(new_user)
    await db.flush()  # Get the user ID without committing
    
    # Create organisation if role is organisation
    if user.role == "organisation" and user.organisation_name:
        new_organisation = Organisation(
            name=user.organisation_name,
            email=user.email,  # Use email instead of domain
            status="pending",  # Set as pending for approval
            plan_type="basic"
        )
        
        db.add(new_organisation)
        await db.flush()  # Get the organisation ID
        
        # Link user to organisation and set user as pending until approved
        new_user.organisation_id = new_organisation.id
        new_user.status = "pending"
        
        logger.info(f"Organisation created with pending status: {user.organisation_name} with user: {user.username}")
    
    # Create company if role is company
    elif user.role == "company" and user.company_name:
        # For company users, we need an organisation first
        if user.organisation_id:
            # Use the selected organisation by ID
            org_result = await db.execute(select(Organisation).where(Organisation.id == user.organisation_id))
            organisation = org_result.scalar_one_or_none()
            
            if not organisation:
                raise HTTPException(status_code=400, detail="Selected organisation not found")
            
            if organisation.status != "active":
                raise HTTPException(status_code=400, detail="Selected organisation is not active")
        elif user.organisation_name:
            # Fallback to organisation name (for backward compatibility)
            org_result = await db.execute(select(Organisation).where(Organisation.name == user.organisation_name))
            organisation = org_result.scalar_one_or_none()
            
            if not organisation:
                raise HTTPException(status_code=400, detail="Organisation not found")
        else:
            raise HTTPException(status_code=400, detail="Organisation is required for company registration")
        
        # Create company
        new_company = Company(
            name=user.company_name,
            organisation_id=organisation.id,
            business_type="Agriculture",
            contact_person=user.full_name,
            email=user.email,
            status="pending",
            notes="self_registered"
        )
        
        db.add(new_company)
        await db.flush()
        
        # Link user to company and organisation
        new_user.company_id = new_company.id
        new_user.organisation_id = organisation.id
        new_user.status = "pending"  # Company users need organisation approval
        
        logger.info(f"Company created: {user.company_name} under organisation: {organisation.name} with user: {user.username}")
    
    await db.commit()
    logger.info(f"User registered: {user.username} with role: {user.role}")
    
    return {
        "message": "User registered successfully",
        "username": user.username,
        "role": user.role
    }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Find user
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check user status and parent entity status
    is_inactive = user.status == "inactive"
    
    if not is_inactive and user.company_id:
        result = await db.execute(select(Company).where(Company.id == user.company_id))
        company = result.scalar_one_or_none()
        if company and company.status == "inactive":
            is_inactive = True
            
    if not is_inactive and user.organisation_id:
        result = await db.execute(select(Organisation).where(Organisation.id == user.organisation_id))
        org = result.scalar_one_or_none()
        if org and org.status == "inactive":
            is_inactive = True

    if is_inactive:
        if user.role == "organisation":
            detail = "account deactivated please contact super admin for more details"
        elif user.role == "company":
            detail = "account deactivated please contact organisation admin for more details"
        else:
            detail = "account deactivated please contact support for more details"
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
    elif user.status == "pending":
        if user.role == "organisation":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your organisation registration is pending approval. Please wait for super admin approval."
            )
        elif user.role == "company":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your company registration is pending approval. Please wait for organisation admin approval."
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval."
        )
    elif user.status == "rejected":
        if user.role == "organisation":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your organisation registration has been rejected. Please contact support for more details."
            )
        elif user.role == "company":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your company registration has been rejected. Please contact your organisation admin."
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been rejected."
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    # Prepare user data
    user_data = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.status == "active",
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    
    logger.info(f"User logged in: {user.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }

@router.post("/login-json", response_model=Token)
async def login_json(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    # Find user
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Check user status and parent entity status
    is_inactive = user.status == "inactive"
    
    if not is_inactive and user.company_id:
        result = await db.execute(select(Company).where(Company.id == user.company_id))
        company = result.scalar_one_or_none()
        if company and company.status == "inactive":
            is_inactive = True
            
    if not is_inactive and user.organisation_id:
        result = await db.execute(select(Organisation).where(Organisation.id == user.organisation_id))
        org = result.scalar_one_or_none()
        if org and org.status == "inactive":
            is_inactive = True

    if is_inactive:
        if user.role == "organisation":
            detail = "account deactivated please contact super admin for more details"
        elif user.role == "company":
            detail = "account deactivated please contact organisation admin for more details"
        else:
            detail = "account deactivated please contact support for more details"
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
    elif user.status == "pending":
        if user.role == "organisation":
            detail = "Your organisation registration is pending approval. Please wait for super admin approval."
        elif user.role == "company":
            detail = "Your company registration is pending approval. Please wait for organisation admin approval."
        else:
            detail = "Your account is pending approval."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
    elif user.status == "rejected":
        if user.role == "organisation":
            detail = "Your organisation registration has been rejected. Please contact support for more details."
        elif user.role == "company":
            detail = "Your company registration has been rejected. Please contact your organisation admin."
        else:
            detail = "Your account has been rejected."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    # Prepare user data
    user_data = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.status == "active",
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    
    logger.info(f"User logged in: {user.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }

@router.get("/me", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_active_user)):
    return current_user

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User logged out: {current_user['username']}")
    return {"message": "Logged out successfully"}

@router.put("/profile")
async def update_profile(
    full_name: Optional[str] = None,
    email: Optional[EmailStr] = None,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Get current user from DB
    result = await db.execute(select(User).where(User.username == current_user["username"]))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if email is already taken
    if email and email != user.email:
        result = await db.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = email
    
    if full_name:
        user.full_name = full_name
    
    await db.commit()
    await db.refresh(user)
    logger.info(f"Profile updated: {user.username}")
    
    # Return updated user
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.status == "active",
        "created_at": user.created_at.isoformat() if user.created_at else None
    }

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Get user from DB
    result = await db.execute(select(User).where(User.username == current_user["username"]))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify old password
    if not verify_password(password_data.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    logger.info(f"Password changed: {user.username}")
    return {"message": "Password changed successfully"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user:
        # To prevent email enumeration, we return success even if user not found
        # but in this specific request "ake that page working", let's be more helpful for now
        raise HTTPException(status_code=404, detail="No account found with this email address")
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    
    await db.commit()
    
    # SIMULATION: Log the reset link since no SMTP is configured
    reset_link = f"http://localhost:3001/reset-password/{token}"
    logger.info(f"PASSWORD RESET REQUEST for {user.username}: {reset_link}")
    print(f"\n*** PASSWORD RESET LINK: {reset_link} ***\n")
    
    return {"message": "Password reset instructions sent to your email (Simulated: Check console/logs)"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    # Find user by token
    result = await db.execute(
        select(User).where(
            (User.reset_token == request.token) & 
            (User.reset_token_expires > datetime.now(timezone.utc))
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    
    await db.commit()
    logger.info(f"Password reset completed for user: {user.username}")
    
    return {"message": "Password reset successfully. You can now login with your new password."}
