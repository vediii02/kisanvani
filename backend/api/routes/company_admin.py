# api/routes/company_admin.py
"""
Company Admin Routes
Each company can manage their own data through their dedicated dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr

from core.auth import get_current_user, get_password_hash, verify_password
from db.session import get_db
from db.models.user import User
from db.models.company import Company
from db.models.product import Product
from db.models.brand import Brand

router = APIRouter(prefix="/company", tags=["Company Admin"])

# ==================== SCHEMAS ====================

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class CompanyProfileUpdate(BaseModel):
    name: Optional[str] = None
    business_type: Optional[str] = None
    brand_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    registration_number: Optional[str] = None
    notes: Optional[str] = None

class CompanyProfile(BaseModel):
    id: int
    organisation_id: int
    name: str
    business_type: Optional[str]
    brand_name: Optional[str]
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
    created_at: str
    
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_products: int
    active_products: int
    total_operators: int
    categories: int

class BrandResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    company_id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]
    subcategory: Optional[str]
    brand_id: Optional[int]
    company_id: int
    status: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== MIDDLEWARE ====================

async def get_current_company_admin(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify that the current user has company role and return user"""
    if current_user.get("role") != "company":
        raise HTTPException(
            status_code=403,
            detail="Access denied. Company role required."
        )
    
    # Get user from database
    query = select(User).where(User.username == current_user["username"])
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not user.company_id:
        raise HTTPException(status_code=400, detail="Company not found for user")
    
    return user

# ==================== ENDPOINTS ====================

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get company dashboard statistics"""
    company_id = current_user.company_id
    
    # Count products for this company
    products_result = await db.execute(
        select(func.count(Product.id)).where(Product.company_id == company_id)
    )
    total_products = products_result.scalar() or 0
    
    # Count active products
    active_result = await db.execute(
        select(func.count(Product.id)).where(
            Product.company_id == company_id,
            Product.is_active == True
        )
    )
    active_products = active_result.scalar() or 0
    
    # Count operators for this company
    operators_result = await db.execute(
        select(func.count(User.id)).where(
            User.company_id == company_id,
            User.role == "operator"
        )
    )
    total_operators = operators_result.scalar() or 0
    
    # Count categories
    categories_result = await db.execute(
        select(func.count(func.distinct(Product.category))).where(
            Product.company_id == company_id
        )
    )
    categories = categories_result.scalar() or 0
    
    return {
        "total_products": total_products,
        "active_products": active_products,
        "total_operators": total_operators,
        "categories": categories
    }

# ==================== PROFILE MANAGEMENT ====================

@router.get("/profile", response_model=CompanyProfile)
async def get_company_profile(
    current_user: User = Depends(get_current_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get company profile"""
    query = select(Company).where(Company.id == current_user.company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return CompanyProfile(
        id=company.id,
        organisation_id=company.organisation_id,
        name=company.name,
        business_type=company.business_type,
        brand_name=company.brand_name,
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
        created_at=company.created_at.isoformat() if company.created_at else ""
    )

@router.put("/profile", response_model=CompanyProfile)
async def update_company_profile(
    profile_update: CompanyProfileUpdate,
    current_user: User = Depends(get_current_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update company profile (company can update their own details)"""
    query = select(Company).where(Company.id == current_user.company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update fields if provided
    if profile_update.name is not None:
        company.name = profile_update.name
    if profile_update.business_type is not None:
        company.business_type = profile_update.business_type
    if profile_update.brand_name is not None:
        company.brand_name = profile_update.brand_name
    if profile_update.contact_person is not None:
        company.contact_person = profile_update.contact_person
    if profile_update.phone is not None:
        company.phone = profile_update.phone
    if profile_update.email is not None:
        company.email = profile_update.email
    if profile_update.address is not None:
        company.address = profile_update.address
    if profile_update.gst_number is not None:
        company.gst_number = profile_update.gst_number
    if profile_update.registration_number is not None:
        company.registration_number = profile_update.registration_number
    if profile_update.notes is not None:
        company.notes = profile_update.notes
    
    company.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(company)
    
    return CompanyProfile(
        id=company.id,
        organisation_id=company.organisation_id,
        name=company.name,
        business_type=company.business_type,
        brand_name=company.brand_name,
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
        created_at=company.created_at.isoformat() if company.created_at else ""
    )

# ==================== PASSWORD MANAGEMENT ====================

@router.patch("/profile/password", status_code=status.HTTP_200_OK)
async def update_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the current company user's password
    Requires current password verification
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "Password updated successfully"}

# ==================== BRANDS & PRODUCTS ====================

@router.get("/brands", response_model=List[BrandResponse])
async def get_company_brands(
    current_user: User = Depends(get_current_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all brands for the current company"""
    query = select(Brand).where(Brand.company_id == current_user.company_id)
    result = await db.execute(query)
    brands = result.scalars().all()
    return brands

@router.get("/products", response_model=List[ProductResponse])
async def get_company_products(
    current_user: User = Depends(get_current_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all products for the current company"""
    query = select(Product).where(Product.company_id == current_user.company_id)
    result = await db.execute(query)
    products = result.scalars().all()
    return products




@router.get("/profile", response_model=CompanyProfile)
async def get_company_profile(
    current_user: User = Depends(get_current_company_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get company profile"""
    query = select(Company).where(Company.id == current_user.company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return CompanyProfile(
        id=company.id,
        organisation_id=company.organisation_id,
        name=company.name,
        business_type=company.business_type,
        brand_name=company.brand_name,
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
        created_at=company.created_at.isoformat() if company.created_at else ""
    )