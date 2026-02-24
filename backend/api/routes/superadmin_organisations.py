# api/routes/superadmin_organisations.py
"""
Super Admin - Organisation Management API
Complete CRUD operations for organisations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone
import logging

from core.auth import get_current_super_admin
from db.session import get_db
from db.models.user import User
from db.models.organisation import Organisation
from db.models.company import Company
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/superadmin/organisations", tags=["Super Admin - Organisations"])

# ==================== SCHEMAS ====================

class OrganisationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    domain: Optional[str] = Field(None, max_length=200)
    status: str = Field(default="active")
    plan_type: str = Field(default="basic")
    primary_phone: Optional[str] = Field(None, max_length=20)
    greeting_message: Optional[str] = None
    preferred_languages: str = Field(default="hi")
    notes: Optional[str] = None
    max_companies: int = Field(default=5, ge=1, le=100)

class OrganisationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    domain: Optional[str] = None
    status: Optional[str] = None
    plan_type: Optional[str] = None
    primary_phone: Optional[str] = None
    greeting_message: Optional[str] = None
    preferred_languages: Optional[str] = None
    notes: Optional[str] = None
    max_companies: Optional[int] = Field(None, ge=1, le=100)

class OrganisationResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    email: Optional[str]
    domain: Optional[str]
    status: str
    plan_type: str
    primary_phone: Optional[str]
    greeting_message: Optional[str]
    preferred_languages: str
    notes: Optional[str]
    max_companies: int
    company_count: int
    user_count: int
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True

class OrganisationListResponse(BaseModel):
    organisations: List[OrganisationResponse]
    total: int
    skip: int
    limit: int

# ==================== ROUTES ====================

@router.get("", response_model=OrganisationListResponse)
async def get_organisations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all organisations with pagination and filters"""
    
    query = select(Organisation)
    
    # Apply filters
    filters = []
    if search:
        filters.append(
            or_(
                Organisation.name.ilike(f"%{search}%"),
                Organisation.email.ilike(f"%{search}%"),
                Organisation.phone.ilike(f"%{search}%")
            )
        )
    if status:
        filters.append(Organisation.status == status)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Get total count
    count_query = select(func.count()).select_from(Organisation)
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(Organisation.created_at.desc())
    result = await db.execute(query)
    organisations = result.scalars().all()
    
    # Get counts for each organisation
    org_responses = []
    for org in organisations:
        # Count companies
        company_count_query = select(func.count()).select_from(Company).where(Company.organisation_id == org.id)
        company_result = await db.execute(company_count_query)
        company_count = company_result.scalar()
        
        # Count users
        user_count_query = select(func.count()).select_from(User).where(User.organisation_id == org.id)
        user_result = await db.execute(user_count_query)
        user_count = user_result.scalar()
        
        org_responses.append(OrganisationResponse(
            id=org.id,
            name=org.name,
            phone=org.phone_numbers if hasattr(org, 'phone_numbers') and org.phone_numbers else None,
            email=None,  # Add email field to org model if needed
            domain=org.domain,
            status=org.status,
            plan_type=org.plan_type,
            primary_phone=org.primary_phone,
            greeting_message=org.greeting_message,
            preferred_languages=org.preferred_languages,
            notes=None,  # Add notes field if needed
            max_companies=10,  # Add to model if needed
            company_count=company_count,
            user_count=user_count,
            created_at=org.created_at.isoformat() if org.created_at else None,
            updated_at=org.updated_at.isoformat() if org.updated_at else None
        ))
    
    return OrganisationListResponse(
        organisations=org_responses,
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/{organisation_id}", response_model=OrganisationResponse)
async def get_organisation(
    organisation_id: int,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get single organisation by ID"""
    
    result = await db.execute(
        select(Organisation).where(Organisation.id == organisation_id)
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Get counts
    company_count_query = select(func.count()).select_from(Company).where(Company.organisation_id == org.id)
    company_result = await db.execute(company_count_query)
    company_count = company_result.scalar()
    
    user_count_query = select(func.count()).select_from(User).where(User.organisation_id == org.id)
    user_result = await db.execute(user_count_query)
    user_count = user_result.scalar()
    
    return OrganisationResponse(
        id=org.id,
        name=org.name,
        phone=org.phone_numbers if hasattr(org, 'phone_numbers') and org.phone_numbers else None,
        email=None,
        domain=org.domain,
        status=org.status,
        plan_type=org.plan_type,
        primary_phone=org.primary_phone,
        greeting_message=org.greeting_message,
        preferred_languages=org.preferred_languages,
        notes=None,
        max_companies=10,
        company_count=company_count,
        user_count=user_count,
        created_at=org.created_at.isoformat() if org.created_at else None,
        updated_at=org.updated_at.isoformat() if org.updated_at else None
    )

@router.post("", response_model=OrganisationResponse, status_code=status.HTTP_201_CREATED)
async def create_organisation(
    org_data: OrganisationCreate,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new organisation and auto-create organisation admin user"""
    
    # Check if domain already exists
    if org_data.domain:
        result = await db.execute(
            select(Organisation).where(Organisation.domain == org_data.domain)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Domain already exists")
    
    # Create organisation
    new_org = Organisation(
        name=org_data.name,
        domain=org_data.domain,
        status=org_data.status,
        plan_type=org_data.plan_type,
        primary_phone=org_data.primary_phone,
        greeting_message=org_data.greeting_message,
        preferred_languages=org_data.preferred_languages,
    )
    
    db.add(new_org)
    await db.commit()
    await db.refresh(new_org)
    
    # Auto-create organisation admin user
    try:
        from core.security import get_password_hash
        from db.models.user import User
        from datetime import datetime, timezone
        
        # Generate default username and password
        username = new_org.domain.split('.')[0] if new_org.domain else f"org_{new_org.id}"
        default_password = f"{username}@123"  # Default password
        email = f"{username}@{new_org.domain}" if new_org.domain else f"{username}@organisation.com"
        
        org_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(default_password),
            full_name=new_org.name,
            role="organisation",
            organisation_id=new_org.id,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(org_user)
        await db.commit()
        await db.refresh(org_user)
        
        logger.info(f"Auto-created user '{username}' for organisation: {new_org.name}")
    except Exception as e:
        logger.warning(f"Failed to auto-create user for organisation {new_org.id}: {e}")
        # Don't fail the organisation creation if user creation fails
    
    logger.info(f"Super admin {current_user['username']} created organisation: {new_org.name}")
    
    return OrganisationResponse(
        id=new_org.id,
        name=new_org.name,
        phone=org_data.phone,
        email=org_data.email,
        domain=new_org.domain,
        status=new_org.status,
        plan_type=new_org.plan_type,
        primary_phone=new_org.primary_phone,
        greeting_message=new_org.greeting_message,
        preferred_languages=new_org.preferred_languages,
        notes=org_data.notes,
        max_companies=org_data.max_companies,
        company_count=0,
        user_count=0,
        created_at=new_org.created_at.isoformat() if new_org.created_at else None,
        updated_at=None
    )

@router.put("/{organisation_id}", response_model=OrganisationResponse)
async def update_organisation(
    organisation_id: int,
    org_data: OrganisationUpdate,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update organisation"""
    
    result = await db.execute(
        select(Organisation).where(Organisation.id == organisation_id)
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Update fields
    update_data = org_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(org, field):
            setattr(org, field, value)
    
    org.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(org)
    
    logger.info(f"Super admin {current_user['username']} updated organisation: {org.name}")
    
    # Get counts
    company_count_query = select(func.count()).select_from(Company).where(Company.organisation_id == org.id)
    company_result = await db.execute(company_count_query)
    company_count = company_result.scalar()
    
    user_count_query = select(func.count()).select_from(User).where(User.organisation_id == org.id)
    user_result = await db.execute(user_count_query)
    user_count = user_result.scalar()
    
    return OrganisationResponse(
        id=org.id,
        name=org.name,
        phone=org_data.phone if org_data.phone else None,
        email=org_data.email if org_data.email else None,
        domain=org.domain,
        status=org.status,
        plan_type=org.plan_type,
        primary_phone=org.primary_phone,
        greeting_message=org.greeting_message,
        preferred_languages=org.preferred_languages,
        notes=org_data.notes if org_data.notes else None,
        max_companies=org_data.max_companies if org_data.max_companies else 10,
        company_count=company_count,
        user_count=user_count,
        created_at=org.created_at.isoformat() if org.created_at else None,
        updated_at=org.updated_at.isoformat() if org.updated_at else None
    )

@router.delete("/{organisation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organisation(
    organisation_id: int,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete organisation (soft delete by setting status to inactive)"""
    
    result = await db.execute(
        select(Organisation).where(Organisation.id == organisation_id)
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Soft delete - just mark as inactive
    org.status = "inactive"
    org.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    logger.info(f"Super admin {current_user['username']} deleted organisation: {org.name}")
    
    return None

@router.post("/{organisation_id}/activate", response_model=dict)
async def activate_organisation(
    organisation_id: int,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Activate organisation"""
    
    result = await db.execute(
        select(Organisation).where(Organisation.id == organisation_id)
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    org.status = "active"
    org.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    logger.info(f"Super admin {current_user['username']} activated organisation: {org.name}")
    
    return {"message": "Organisation activated successfully", "organisation_id": org.id}

@router.get("/{organisation_id}/companies", response_model=dict)
async def get_organisation_companies(
    organisation_id: int,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all companies for an organisation"""
    
    result = await db.execute(
        select(Company).where(Company.organisation_id == organisation_id).order_by(Company.created_at.desc())
    )
    companies = result.scalars().all()
    
    return {
        "organisation_id": organisation_id,
        "companies": [
            {
                "id": c.id,
                "name": c.name,
                "business_type": c.business_type,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in companies
        ],
        "total": len(companies)
    }

@router.get("/{organisation_id}/users", response_model=dict)
async def get_organisation_users(
    organisation_id: int,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all users for an organisation"""
    
    result = await db.execute(
        select(User).where(User.organisation_id == organisation_id).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    return {
        "organisation_id": organisation_id,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ],
        "total": len(users)
    }
