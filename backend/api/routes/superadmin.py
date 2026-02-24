from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.session import get_db
from db.models.user import User
from db.models.company import Company
from db.models.organisation import Organisation
from db.models.brand import Brand
from db.models.product import Product
from core.auth import get_current_super_admin, get_password_hash
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/superadmin", tags=["superadmin"])

# Pydantic models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    role: str = Field(..., pattern="^(operator|admin|supervisor|superadmin)$")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(operator|admin|supervisor|superadmin)$")
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str

class DashboardStats(BaseModel):
    total_users: int
    total_admins: int
    total_operators: int
    total_supervisors: int
    active_users: int
    inactive_users: int

class CompanyResponse(BaseModel):
    id: int
    name: str
    organisation_id: int
    organisation_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    status: str
    is_active: bool
    brand_count: int = 0
    product_count: int = 0
    created_at: str

class CompanyCreate(BaseModel):
    name: str
    organisation_id: int
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

# Get all users
@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Get all users (Super Admin only)"""
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email or "",
            full_name=user.full_name or "",
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else ""
        )
        for user in users
    ]

# Get user by ID
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Get a specific user by ID (Super Admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email or "",
        full_name=user.full_name or "",
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )

# Create new user
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Create a new user (Super Admin only)"""
    # Check if username or email already exists
    result = await db.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"Super Admin {current_user['username']} created user: {new_user.username}")
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email or "",
        full_name=new_user.full_name or "",
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat() if new_user.created_at else ""
    )

# Update user
@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Update a user (Super Admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if email is being changed and if it's already taken
    if user_data.email and user_data.email != user.email:
        result = await db.execute(select(User).where(User.email == user_data.email))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_data.email
    
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.role is not None:
        user.role = user_data.role
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"Super Admin {current_user['username']} updated user: {user.username}")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email or "",
        full_name=user.full_name or "",
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )

# Delete user
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Delete a user (Super Admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-deletion
    if user.username == current_user['username']:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    await db.delete(user)
    await db.commit()
    
    logger.info(f"Super Admin {current_user['username']} deleted user: {user.username}")
    
    return {"message": f"User {user.username} deleted successfully"}

# Get dashboard stats
@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_superadmin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Get super admin dashboard statistics"""
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar()
    
    total_admins_result = await db.execute(
        select(func.count(User.id)).where(User.role == "admin")
    )
    total_admins = total_admins_result.scalar()
    
    total_operators_result = await db.execute(
        select(func.count(User.id)).where(User.role == "operator")
    )
    total_operators = total_operators_result.scalar()
    
    total_supervisors_result = await db.execute(
        select(func.count(User.id)).where(User.role == "supervisor")
    )
    total_supervisors = total_supervisors_result.scalar()
    
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar()
    
    inactive_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == False)
    )
    inactive_users = inactive_users_result.scalar()
    
    return DashboardStats(
        total_users=total_users,
        total_admins=total_admins,
        total_operators=total_operators,
        total_supervisors=total_supervisors,
        active_users=active_users,
        inactive_users=inactive_users
    )

# Reset user password
class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6)

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Reset a user's password (Super Admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    logger.info(f"Super Admin {current_user['username']} reset password for user: {user.username}")
    
    return {"message": f"Password reset successfully for user {user.username}"}

# ===========================
# Company Management Routes
# ===========================

@router.get("/companies", response_model=List[CompanyResponse])
async def get_all_companies(
    skip: int = 0,
    limit: int = 100,
    organisation_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Get all companies across all organisations"""
    query = select(Company, Organisation.name.label("org_name")).join(
        Organisation, Company.organisation_id == Organisation.id
    )
    
    if organisation_id:
        query = query.where(Company.organisation_id == organisation_id)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    
    companies_list = []
    for company, org_name in rows:
        # Count brands
        brand_count_result = await db.execute(
            select(func.count(Brand.id)).where(Brand.company_id == company.id)
        )
        brand_count = brand_count_result.scalar() or 0
        
        # Count products
        product_count_result = await db.execute(
            select(func.count(Product.id)).where(Product.company_id == company.id)
        )
        product_count = product_count_result.scalar() or 0
        
        companies_list.append(CompanyResponse(
            id=company.id,
            name=company.name,
            organisation_id=company.organisation_id,
            organisation_name=org_name,
            contact_person=company.contact_person,
            phone=company.phone,
            email=company.email,
            address=company.address,
            status=company.status,
            is_active=company.status == "active",
            brand_count=brand_count,
            product_count=product_count,
            created_at=company.created_at.isoformat() if company.created_at else ""
        ))
    
    return companies_list

@router.post("/companies", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Create a new company and auto-create company admin user"""
    # Check if organisation exists
    org_result = await db.execute(
        select(Organisation).where(Organisation.id == company_data.organisation_id)
    )
    organisation = org_result.scalar_one_or_none()
    
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Create company
    new_company = Company(
        name=company_data.name,
        organisation_id=company_data.organisation_id,
        contact_person=company_data.contact_person,
        phone=company_data.phone,
        email=company_data.email,
        address=company_data.address,
        status="active" if company_data.is_active else "inactive"
    )
    
    db.add(new_company)
    await db.commit()
    await db.refresh(new_company)
    
    # Auto-create company admin user
    try:
        from core.security import get_password_hash
        from db.models.user import User
        from datetime import datetime, timezone
        
        # Generate default username from company name
        username = new_company.name.lower().replace(' ', '_').replace('-', '_')[:20]
        # Make username unique by appending company_id if needed
        check_user = await db.execute(select(User).where(User.username == username))
        if check_user.scalar_one_or_none():
            username = f"{username}_{new_company.id}"
        
        default_password = f"{username}@123"
        email = new_company.email or f"{username}@{organisation.domain}" if organisation.domain else f"{username}@company.com"
        
        company_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(default_password),
            full_name=new_company.name,
            role="company",
            organisation_id=new_company.organisation_id,
            company_id=new_company.id,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(company_user)
        await db.commit()
        await db.refresh(company_user)
        
        logger.info(f"Auto-created user '{username}' for company: {new_company.name}")
    except Exception as e:
        logger.warning(f"Failed to auto-create user for company {new_company.id}: {e}")
        # Don't fail company creation if user creation fails
    
    logger.info(f"Super Admin {current_user['username']} created company: {new_company.name}")
    
    return CompanyResponse(
        id=new_company.id,
        name=new_company.name,
        organisation_id=new_company.organisation_id,
        organisation_name=organisation.name,
        contact_person=new_company.contact_person,
        phone=new_company.phone,
        email=new_company.email,
        address=new_company.address,
        status=new_company.status,
        is_active=new_company.status == "active",
        brand_count=0,
        product_count=0,
        created_at=new_company.created_at.isoformat()
    )

@router.put("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Update a company"""
    result = await db.execute(
        select(Company, Organisation.name.label("org_name")).join(
            Organisation, Company.organisation_id == Organisation.id
        ).where(Company.id == company_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company, org_name = row
    
    # Update fields
    if company_data.name is not None:
        company.name = company_data.name
    if company_data.contact_person is not None:
        company.contact_person = company_data.contact_person
    if company_data.phone is not None:
        company.phone = company_data.phone
    if company_data.email is not None:
        company.email = company_data.email
    if company_data.address is not None:
        company.address = company_data.address
    if company_data.is_active is not None:
        company.status = "active" if company_data.is_active else "inactive"
    
    await db.commit()
    await db.refresh(company)
    
    # Get counts
    brand_count_result = await db.execute(
        select(func.count(Brand.id)).where(Brand.company_id == company.id)
    )
    brand_count = brand_count_result.scalar() or 0
    
    product_count_result = await db.execute(
        select(func.count(Product.id)).where(Product.company_id == company.id)
    )
    product_count = product_count_result.scalar() or 0
    
    logger.info(f"Super Admin {current_user['username']} updated company: {company.name}")
    
    return CompanyResponse(
        id=company.id,
        name=company.name,
        organisation_id=company.organisation_id,
        organisation_name=org_name,
        contact_person=company.contact_person,
        phone=company.phone,
        email=company.email,
        address=company.address,
        status=company.status,
        is_active=company.status == "active",
        brand_count=brand_count,
        product_count=product_count,
        created_at=company.created_at.isoformat()
    )

@router.delete("/companies/{company_id}")
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Delete a company"""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    await db.delete(company)
    await db.commit()
    
    logger.info(f"Super Admin {current_user['username']} deleted company: {company.name}")
    
    return {"message": "Company deleted successfully"}

@router.get("/organisations")
async def get_organisations_list(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Get list of all organisations for dropdowns"""
    result = await db.execute(select(Organisation))
    organisations = result.scalars().all()
    
    return [
        {"id": org.id, "name": org.name}
        for org in organisations
    ]
