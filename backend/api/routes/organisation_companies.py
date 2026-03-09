# api/routes/organisation_companies.py
"""
Organisation Admin - Company Management API
Organisation admins can manage companies within their organisation
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime, timezone
import logging

from core.auth import get_current_user, get_password_hash
from db.session import get_db
from db.models.user import User
from db.models.company import Company
from db.models.product import Product
from db.models.brand import Brand
from db.models.call_session import CallSession
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organisation/companies", tags=["Organisation Admin - Companies"])

# ==================== SCHEMAS ====================

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    business_type: Optional[str] = Field(None, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gst_number: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="active")
    max_operators: int = Field(default=5, ge=1, le=50)
    max_products: int = Field(default=100, ge=1, le=10000)
    notes: Optional[str] = None
    # User credentials for company login
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=6)

class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    business_type: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    registration_number: Optional[str] = None
    status: Optional[str] = None
    max_operators: Optional[int] = Field(None, ge=1, le=50)
    max_products: Optional[int] = Field(None, ge=1, le=10000)
    notes: Optional[str] = None

class CompanyResponse(BaseModel):
    id: int
    organisation_id: int
    name: str
    business_type: Optional[str]
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    gst_number: Optional[str]
    registration_number: Optional[str]
    status: str
    max_operators: int
    max_products: int
    notes: Optional[str]
    operator_count: int
    product_count: int
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True

class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]
    total: int
    skip: int
    limit: int

# ==================== HELPER FUNCTIONS ====================

async def check_organisation_access(user: dict, db: AsyncSession):
    """Verify user is organisation admin"""
    if user.get("role") not in ["organisation", "organisation_admin", "admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organisation admins can manage companies"
        )
    return user.get("organisation_id") if user.get("role") in ["organisation", "organisation_admin"] else None

# ==================== ROUTES ====================

@router.get("", response_model=CompanyListResponse)
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all companies for the organisation"""
    
    org_id = await check_organisation_access(current_user, db)
    
    # If admin/superadmin and no org_id provided in user, show all
    if current_user.get("role") in ["admin", "superadmin"] and not org_id:
        query = select(Company)
    else:
        if not org_id:
            raise HTTPException(status_code=400, detail="Organisation ID not found for user")
        query = select(Company).where(Company.organisation_id == org_id)
    
    # Apply filters
    if search:
        query = query.where(Company.name.ilike(f"%{search}%"))
    
    if status:
        query = query.where(Company.status == status)
    else:
        # Show active and inactive companies only
        query = query.where(Company.status.in_(['active', 'inactive']))
    
    # Get total count
    count_query = select(func.count()).select_from(Company)
    if org_id:
        count_query = count_query.where(Company.organisation_id == org_id)
    if search:
        count_query = count_query.where(Company.name.ilike(f"%{search}%"))
    
    if status:
        count_query = count_query.where(Company.status == status)
    else:
        # Show active and inactive companies only
        count_query = count_query.where(Company.status.in_(['active', 'inactive']))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(Company.created_at.desc())
    result = await db.execute(query)
    companies = result.scalars().all()
    
    # Get counts for each company
    company_responses = []
    for company in companies:
        # Count operators
        operator_count_query = select(func.count()).select_from(User).where(User.company_id == company.id)
        operator_result = await db.execute(operator_count_query)
        operator_count = operator_result.scalar()
        
        # Count products
        product_count_query = select(func.count()).select_from(Product).where(Product.company_id == company.id)
        product_result = await db.execute(product_count_query)
        product_count = product_result.scalar()
        
        company_responses.append(CompanyResponse(
            id=company.id,
            organisation_id=company.organisation_id,
            name=company.name,
            business_type=company.business_type,
            contact_person=company.contact_person,
            phone=company.phone,
            email=company.email,
            address=company.address,
            gst_number=company.gst_number,
            registration_number=company.registration_number,
            status=company.status,
            max_operators=company.max_operators,
            max_products=company.max_products,
            notes=company.notes,
            operator_count=operator_count,
            product_count=product_count,
            created_at=company.created_at.isoformat() if company.created_at else None,
            updated_at=company.updated_at.isoformat() if company.updated_at else None
        ))
    
    return CompanyListResponse(
        companies=company_responses,
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single company by ID"""
    
    org_id = await check_organisation_access(current_user, db)
    
    query = select(Company).where(Company.id == company_id)
    if org_id:
        query = query.where(Company.organisation_id == org_id)
    
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get counts
    operator_count_query = select(func.count()).select_from(User).where(User.company_id == company.id)
    operator_result = await db.execute(operator_count_query)
    operator_count = operator_result.scalar()
    
    product_count_query = select(func.count()).select_from(Product).where(Product.company_id == company.id)
    product_result = await db.execute(product_count_query)
    product_count = product_result.scalar()
    
    return CompanyResponse(
        id=company.id,
        organisation_id=company.organisation_id,
        name=company.name,
        business_type=company.business_type,
        contact_person=company.contact_person,
        phone=company.phone,
        email=company.email,
        address=company.address,
        gst_number=company.gst_number,
        registration_number=company.registration_number,
        status=company.status,
        max_operators=company.max_operators,
        max_products=company.max_products,
        notes=company.notes,
        operator_count=operator_count,
        product_count=product_count,
        created_at=company.created_at.isoformat() if company.created_at else None,
        updated_at=company.updated_at.isoformat() if company.updated_at else None
    )

@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new company and auto-create company user if credentials provided"""
    
    org_id = await check_organisation_access(current_user, db)
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organisation ID not found for user")
    
    # If username/password provided, validate and check for duplicates
    if company_data.username or company_data.password:
        if not company_data.username:
            raise HTTPException(status_code=400, detail="Username is required if password is provided")
        if not company_data.password:
            raise HTTPException(status_code=400, detail="Password is required if username is provided")
        if not company_data.email:
            raise HTTPException(status_code=400, detail="Email is required for company login")
        
        # Check if username already exists
        user_query = select(User).where(User.username == company_data.username)
        user_result = await db.execute(user_query)
        existing_user = user_result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(status_code=400, detail=f"Username '{company_data.username}' already exists")
        
        # Check if email already exists
        email_query = select(User).where(User.email == company_data.email)
        email_result = await db.execute(email_query)
        existing_email = email_result.scalar_one_or_none()
        if existing_email:
            raise HTTPException(status_code=400, detail=f"Email '{company_data.email}' already exists")
    
        # Create company
        new_company = Company(
            organisation_id=org_id,
            name=company_data.name,
            business_type=company_data.business_type,
            contact_person=company_data.contact_person,
            phone=company_data.phone,
            email=company_data.email,
            address=company_data.address,
            gst_number=company_data.gst_number,
            registration_number=company_data.registration_number,
            status=company_data.status,
            max_operators=company_data.max_operators,
            max_products=company_data.max_products,
            notes=company_data.notes
        )
        
        try:
            db.add(new_company)
            await db.commit()
            await db.refresh(new_company)
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating company (DB): {str(e)}")
            # Sometimes SQLAlchemy errors mention duplicate key
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                raise HTTPException(status_code=400, detail="A company with these details already exists.")
            raise HTTPException(status_code=500, detail="Database error occurred while creating company.")
        
        # Create user for company if credentials provided
        company_user = None
        if company_data.username and company_data.password:
            company_user = User(
                username=company_data.username,
                email=company_data.email,
                hashed_password=get_password_hash(company_data.password),
                full_name=company_data.name,
                role="company",
                organisation_id=org_id,
                company_id=new_company.id,
                status=company_data.status,
                created_at=datetime.now(timezone.utc)
            )
            
            try:
                db.add(company_user)
                await db.commit()
                await db.refresh(company_user)
            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating company user: {str(e)}")
                # If user creation fails, we should ideally rollback company creation too,
                # but since it's already committed, we return an error indicating partial success
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    raise HTTPException(status_code=400, detail="Company created, but user creation failed: Username or Email already exists.")
                raise HTTPException(status_code=500, detail="Company created, but failed to create user credentials.")
        
        logger.info(f"User {current_user['username']} created company: {new_company.name}")
        
        return CompanyResponse(
            id=new_company.id,
            organisation_id=new_company.organisation_id,
            name=new_company.name,
            business_type=new_company.business_type,
            contact_person=new_company.contact_person,
            phone=new_company.phone,
            email=new_company.email,
            address=new_company.address,
            gst_number=new_company.gst_number,
            registration_number=new_company.registration_number,
            status=new_company.status,
            max_operators=new_company.max_operators,
            max_products=new_company.max_products,
            notes=new_company.notes,
            operator_count=0,
            product_count=0,
            created_at=new_company.created_at.isoformat() if new_company.created_at else None,
            updated_at=new_company.updated_at.isoformat() if new_company.updated_at else None
        )

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update company"""
    
    org_id = await check_organisation_access(current_user, db)
    
    query = select(Company).where(Company.id == company_id)
    if org_id:
        query = query.where(Company.organisation_id == org_id)
    
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update fields
    update_data = company_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    company.updated_at = datetime.now(timezone.utc)
    
    # Sync with company admin user
    admin_user_result = await db.execute(
        select(User).where(User.company_id == company.id, User.role == 'company')
    )
    admin_user = admin_user_result.scalars().first()
    if admin_user:
        if company_data.name is not None:
            admin_user.full_name = company_data.name
        if company_data.email is not None and company_data.email != admin_user.email:
            admin_user.email = company_data.email
        if company_data.status is not None:
            admin_user.status = company_data.status
        db.add(admin_user)
        
    await db.commit()
    await db.refresh(company)
    
    logger.info(f"User {current_user['username']} updated company: {company.name}")
    
    # Get counts
    operator_count_query = select(func.count()).select_from(User).where(User.company_id == company.id)
    operator_result = await db.execute(operator_count_query)
    operator_count = operator_result.scalar()
    
    product_count_query = select(func.count()).select_from(Product).where(Product.company_id == company.id)
    product_result = await db.execute(product_count_query)
    product_count = product_result.scalar()
    
    return CompanyResponse(
        id=company.id,
        organisation_id=company.organisation_id,
        name=company.name,
        business_type=company.business_type,
        contact_person=company.contact_person,
        phone=company.phone,
        email=company.email,
        address=company.address,
        gst_number=company.gst_number,
        registration_number=company.registration_number,
        status=company.status,
        max_operators=company.max_operators,
        max_products=company.max_products,
        notes=company.notes,
        operator_count=operator_count,
        product_count=product_count,
        created_at=company.created_at.isoformat() if company.created_at else None,
        updated_at=company.updated_at.isoformat() if company.updated_at else None
    )

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete company (hard delete)"""
    
    org_id = await check_organisation_access(current_user, db)
    
    query = select(Company).where(Company.id == company_id)
    if org_id:
        query = query.where(Company.organisation_id == org_id)
    
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_name = company.name
    # Hard delete - database cascades will handle related records
    await db.delete(company)
    await db.commit()
    
    logger.info(f"User {current_user['username']} deleted company: {company_name}")
    
    return None
@router.get("/stats/summary")
async def get_organisation_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get summarized statistics for the organisation dashboard"""
    org_id = await check_organisation_access(current_user, db)
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organisation ID not found for user")

    # Company stats
    company_total_res = await db.execute(select(func.count(Company.id)).where(Company.organisation_id == org_id))
    company_total = company_total_res.scalar() or 0
    
    company_active_res = await db.execute(select(func.count(Company.id)).where(and_(Company.organisation_id == org_id, Company.status == "active")))
    company_active = company_active_res.scalar() or 0
    
    # Brand stats
    brand_total_res = await db.execute(select(func.count(Brand.id)).where(Brand.organisation_id == org_id))
    brand_total = brand_total_res.scalar() or 0
    
    brand_active_res = await db.execute(select(func.count(Brand.id)).where(and_(Brand.organisation_id == org_id, Brand.is_active == True)))
    brand_active = brand_active_res.scalar() or 0
    
    # Product stats
    product_total_res = await db.execute(select(func.count(Product.id)).where(Product.organisation_id == org_id))
    product_total = product_total_res.scalar() or 0
    
    product_active_res = await db.execute(select(func.count(Product.id)).where(and_(Product.organisation_id == org_id, Product.is_active == True)))
    product_active = product_active_res.scalar() or 0
    
    # Call stats
    call_total_res = await db.execute(select(func.count(CallSession.id)).where(CallSession.organisation_id == org_id))
    call_total = call_total_res.scalar() or 0

    return {
        "totalCompanies": company_total,
        "activeCompanies": company_active,
        "inactiveCompanies": company_total - company_active,
        "totalBrands": brand_total,
        "activeBrands": brand_active,
        "inactiveBrands": brand_total - brand_active,
        "totalProducts": product_total,
        "activeProducts": product_active,
        "inactiveProducts": product_total - product_active,
        "totalCalls": call_total
    }
