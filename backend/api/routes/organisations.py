from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from db.session import get_db
from db.models.organisation import Organisation
from db.models.organisation_phone import OrganisationPhoneNumber
from db.models.brand import Brand
from db.models.product import Product
from core.auth import get_current_super_admin, get_current_user
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import json
import csv
import io
from datetime import datetime, timezone
try:
    import openpyxl
except ImportError:
    openpyxl = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organisations", tags=["organisations"])

# ==================== Pydantic Models ====================

class OrganisationCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    status: str = Field(default="active", pattern="^(active|inactive|suspended)$")
    plan_type: str = Field(default="basic", pattern="^(basic|professional|enterprise)$")
    phone_numbers: Optional[str] = Field(None, max_length=20)
    secondary_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=1000)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    website_link: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)

class OrganisationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")
    plan_type: Optional[str] = Field(None, pattern="^(basic|professional|enterprise)$")
    phone_numbers: Optional[str] = Field(None, max_length=20)
    secondary_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=1000)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    website_link: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)

class OrganisationResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    status: str
    plan_type: str
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    website_link: Optional[str]
    description: Optional[str]
    phone_numbers: Optional[str]
    secondary_phone: Optional[str]
    created_at: str
    updated_at: Optional[str]

class PhoneNumberCreate(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)
    channel: str = Field(default="voice", pattern="^(voice|whatsapp|sms)$")
    region: Optional[str] = None

class PhoneNumberResponse(BaseModel):
    id: int
    organisation_id: int
    phone_number: str
    channel: str
    status: str
    region: Optional[str]
    created_at: str

class BrandCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    organisation_id: Optional[int] = None
    company_id: Optional[int] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool = True

class BrandResponse(BaseModel):
    id: int
    name: str
    organisation_id: int
    company_id: Optional[int] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool = True
    created_at: str
    product_count: Optional[int] = 0

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    company_id: int
    brand_id: Optional[int] = None
    category: Optional[str] = "other"
    sub_category: Optional[str] = None
    description: Optional[str] = None
    target_crops: Optional[str] = None
    target_problems: Optional[str] = None
    dosage: Optional[str] = None
    usage_instructions: Optional[str] = None
    safety_precautions: Optional[str] = None
    price_range: Optional[str] = None
    is_active: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    company_id: Optional[int] = None
    brand_id: Optional[int] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None
    target_crops: Optional[str] = None
    target_problems: Optional[str] = None
    dosage: Optional[str] = None
    usage_instructions: Optional[str] = None
    safety_precautions: Optional[str] = None
    price_range: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    organisation_id: int
    company_id: Optional[int]
    brand_id: Optional[int]
    brand_name: Optional[str] = None
    company_name: Optional[str] = None
    category: Optional[str]
    sub_category: Optional[str]
    description: Optional[str]
    target_crops: Optional[str]
    target_problems: Optional[str]
    dosage: Optional[str]
    usage_instructions: Optional[str]
    safety_precautions: Optional[str]
    price_range: Optional[str]
    is_active: bool
    created_at: Optional[str]

# ==================== Organisation Profile ====================

@router.get("/profile", response_model=OrganisationResponse)
async def get_my_organisation_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current logged-in organisation's profile details"""
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User not associated with any organisation")
    
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    return OrganisationResponse(
        id=org.id,
        name=org.name,
        email=org.email,
        status=org.status,
        plan_type=org.plan_type,
        phone_numbers=org.phone_numbers,
        secondary_phone=org.secondary_phone,
        address=org.address,
        city=org.city,
        state=org.state,
        pincode=org.pincode,
        website_link=org.website_link,
        description=org.description,
        created_at=org.created_at.isoformat() if org.created_at else "",
        updated_at=org.updated_at.isoformat() if org.updated_at else None
    )

@router.put("/profile", response_model=OrganisationResponse)
async def update_my_organisation_profile(
    org_data: OrganisationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update current logged-in organisation's profile"""
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User not associated with any organisation")
    
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Update fields
    update_data = org_data.model_dump(exclude_unset=True)
    
    # Check email uniqueness if being changed
    if "email" in update_data and update_data["email"] != org.email:
        email_check = await db.execute(
            select(Organisation).where(Organisation.email == update_data["email"])
        )
        if email_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")
    
    # Phone numbers uniqueness check omitted for now

    for field, value in update_data.items():
        setattr(org, field, value)
    
    # Synchronize phone_numbers list with individual fields deleted - consolidation complete
    
    org.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(org)
    
    logger.info(f"Organisation Admin {current_user['username']} updated profile: {org.name}")
    
    return OrganisationResponse(
        id=org.id,
        name=org.name,
        email=org.email,
        status=org.status,
        plan_type=org.plan_type,
        phone_numbers=org.phone_numbers,
        secondary_phone=org.secondary_phone,
        address=org.address,
        city=org.city,
        state=org.state,
        pincode=org.pincode,
        website_link=org.website_link,
        description=org.description,
        created_at=org.created_at.isoformat() if org.created_at else "",
        updated_at=org.updated_at.isoformat() if org.updated_at else None
    )

# ==================== Organisation CRUD ====================

@router.get("/", response_model=List[OrganisationResponse])
async def get_all_organisations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Get all organisations (Super Admin only)"""
    result = await db.execute(select(Organisation).offset(skip).limit(limit))
    orgs = result.scalars().all()
    
    return [
        OrganisationResponse(
            id=org.id,
            name=org.name,
            email=org.email,
            status=org.status,
            plan_type=org.plan_type,
            phone_numbers=org.phone_numbers,
            secondary_phone=org.secondary_phone,
            address=org.address,
            city=org.city,
            state=org.state,
            pincode=org.pincode,
            website_link=org.website_link,
            description=org.description,
            created_at=org.created_at.isoformat() if org.created_at else "",
            updated_at=org.updated_at.isoformat() if org.updated_at else None
        )
        for org in orgs
    ]

@router.get("/{org_id}", response_model=OrganisationResponse)
async def get_organisation(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Get organisation by ID"""
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    return OrganisationResponse(
        id=org.id,
        name=org.name,
        email=org.email,
        status=org.status,
        plan_type=org.plan_type,
        phone_numbers=org.phone_numbers,
        secondary_phone=org.secondary_phone,
        address=org.address,
        city=org.city,
        state=org.state,
        pincode=org.pincode,
        website_link=org.website_link,
        description=org.description,
        created_at=org.created_at.isoformat() if org.created_at else "",
        updated_at=org.updated_at.isoformat() if org.updated_at else None
    )

@router.post("/", response_model=OrganisationResponse)
async def create_organisation(
    org_data: OrganisationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Create new organisation"""
    # Check if email already exists
    if org_data.email:
        result = await db.execute(
            select(Organisation).where(Organisation.email == org_data.email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    new_org = Organisation(
        name=org_data.name,
        email=org_data.email,
        status=org_data.status,
        plan_type=org_data.plan_type,
        phone_numbers=org_data.phone_numbers,
        secondary_phone=org_data.secondary_phone,
        address=org_data.address,
        city=org_data.city,
        state=org_data.state,
        pincode=org_data.pincode,
        website_link=org_data.website_link,
        description=org_data.description
    )
    
    db.add(new_org)
    await db.commit()
    await db.refresh(new_org)
    
    logger.info(f"Super Admin {current_user['username']} created organisation: {new_org.name}")
    
    return OrganisationResponse(
        id=new_org.id,
        name=new_org.name,
        email=new_org.email,
        status=new_org.status,
        plan_type=new_org.plan_type,
        phone_numbers=new_org.phone_numbers,
        secondary_phone=new_org.secondary_phone,
        address=new_org.address,
        city=new_org.city,
        state=new_org.state,
        pincode=new_org.pincode,
        website_link=new_org.website_link,
        description=new_org.description,
        created_at=new_org.created_at.isoformat() if new_org.created_at else "",
        updated_at=None
    )

@router.put("/{org_id}", response_model=OrganisationResponse)
async def update_organisation(
    org_id: int,
    org_data: OrganisationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Update organisation"""
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Check email uniqueness if being changed
    if org_data.email and org_data.email != org.email:
        result = await db.execute(
            select(Organisation).where(Organisation.email == org_data.email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        org.email = org_data.email
    
    if org_data.name:
        org.name = org_data.name
    if org_data.status:
        org.status = org_data.status
    if org_data.plan_type:
        org.plan_type = org_data.plan_type
    
    await db.commit()
    await db.refresh(org)
    
    logger.info(f"Super Admin {current_user['username']} updated organisation: {org.name}")
    
    return OrganisationResponse(
        id=org.id,
        name=org.name,
        email=org.email,
        status=org.status,
        plan_type=org.plan_type,
        phone_numbers=org.phone_numbers,
        secondary_phone=org.secondary_phone,
        address=org.address,
        city=org.city,
        state=org.state,
        pincode=org.pincode,
        website_link=org.website_link,
        description=org.description,
        created_at=org.created_at.isoformat() if org.created_at else "",
        updated_at=org.updated_at.isoformat() if org.updated_at else None
    )

@router.delete("/{org_id}")
async def delete_organisation(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Delete organisation"""
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Prevent deleting default organisation
    if org.id == 1:
        raise HTTPException(status_code=400, detail="Cannot delete default organisation")
    
    await db.delete(org)
    await db.commit()
    
    logger.info(f"Super Admin {current_user['username']} deleted organisation: {org.name}")
    
    return {"message": f"Organisation {org.name} deleted successfully"}

# ==================== Phone Number Management ====================

@router.get("/{org_id}/phones", response_model=List[PhoneNumberResponse])
async def get_organisation_phones(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Get all phone numbers for an organisation"""
    result = await db.execute(
        select(OrganisationPhoneNumber).where(OrganisationPhoneNumber.organisation_id == org_id)
    )
    phones = result.scalars().all()
    
    return [
        PhoneNumberResponse(
            id=phone.id,
            organisation_id=phone.organisation_id,
            phone_number=phone.phone_number,
            channel=phone.channel,
            status=phone.status,
            region=phone.region,
            created_at=phone.created_at.isoformat() if phone.created_at else ""
        )
        for phone in phones
    ]

@router.post("/{org_id}/phones", response_model=PhoneNumberResponse)
async def add_phone_number(
    org_id: int,
    phone_data: PhoneNumberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Assign phone number to organisation"""
    # Check if phone number already exists
    result = await db.execute(
        select(OrganisationPhoneNumber).where(
            OrganisationPhoneNumber.phone_number == phone_data.phone_number
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already assigned")
    
    new_phone = OrganisationPhoneNumber(
        organisation_id=org_id,
        phone_number=phone_data.phone_number,
        channel=phone_data.channel,
        region=phone_data.region,
        status="active"
    )
    
    db.add(new_phone)
    await db.commit()
    await db.refresh(new_phone)
    
    logger.info(f"Super Admin added phone {phone_data.phone_number} to org {org_id}")
    
    return PhoneNumberResponse(
        id=new_phone.id,
        organisation_id=new_phone.organisation_id,
        phone_number=new_phone.phone_number,
        channel=new_phone.channel,
        status=new_phone.status,
        region=new_phone.region,
        created_at=new_phone.created_at.isoformat() if new_phone.created_at else ""
    )

@router.delete("/{org_id}/phones/{phone_id}")
async def remove_phone_number(
    org_id: int,
    phone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Remove phone number from organisation"""
    result = await db.execute(
        select(OrganisationPhoneNumber).where(
            OrganisationPhoneNumber.id == phone_id,
            OrganisationPhoneNumber.organisation_id == org_id
        )
    )
    phone = result.scalar_one_or_none()
    
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")
    
    await db.delete(phone)
    await db.commit()
    
    logger.info(f"Super Admin removed phone {phone.phone_number} from org {org_id}")
    
    return {"message": "Phone number removed successfully"}

# ==================== Brand Management ====================

@router.get("/{org_id}/brands", response_model=List[BrandResponse])
async def get_organisation_brands(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Get all brands for an organisation"""
    result = await db.execute(
        select(Brand).where(Brand.organisation_id == org_id)
    )
    brands = result.scalars().all()
    
    return [
        BrandResponse(
            id=brand.id,
            name=brand.name,
            organisation_id=brand.organisation_id,
            company_id=brand.company_id,
            description=brand.description,
            logo_url=brand.logo_url,
            is_active=brand.is_active,
            created_at=brand.created_at.isoformat() if brand.created_at else "",
            product_count=0 # Placeholder, can be calculated if needed
        )
        for brand in brands
    ]

@router.post("/{org_id}/brands", response_model=BrandResponse)
async def create_brand(
    org_id: int,
    brand_data: BrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Create brand for organisation"""
    new_brand = Brand(
        organisation_id=org_id,
        company_id=brand_data.company_id,
        name=brand_data.name,
        description=brand_data.description,
        logo_url=brand_data.logo_url,
        is_active=True
    )
    
    db.add(new_brand)
    await db.commit()
    await db.refresh(new_brand)
    
    logger.info(f"Created brand {brand_data.name} for org {org_id}, company {brand_data.company_id}")
    
    return BrandResponse(
        id=new_brand.id,
        name=new_brand.name,
        organisation_id=new_brand.organisation_id,
        company_id=new_brand.company_id,
        description=new_brand.description,
        logo_url=new_brand.logo_url,
        is_active=new_brand.is_active,
        created_at=new_brand.created_at.isoformat() if new_brand.created_at else "",
        product_count=0
    )

# (Product Management moved to product_router at the bottom)


# ==================== Phone Number Lookup (For Call Routing) ====================

@router.get("/lookup/phone/{phone_number}")
async def lookup_organisation_by_phone(
    phone_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Lookup organisation by phone number (for call routing)"""
    result = await db.execute(
        select(OrganisationPhoneNumber).where(
            OrganisationPhoneNumber.phone_number == phone_number,
            OrganisationPhoneNumber.status == "active"
        )
    )
    phone = result.scalar_one_or_none()
    
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not mapped to any organisation")
    
    # Get organisation details
    org_result = await db.execute(
        select(Organisation).where(Organisation.id == phone.organisation_id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    return {
        "organisation_id": org.id,
        "organisation_name": org.name,
        "status": org.status,
        "phone_number": phone.phone_number,
        "channel": phone.channel
    }


# ==================== Brand Management ====================

# (Duplicate BrandCreate removed)

class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    organisation_id: Optional[int] = None
    company_id: Optional[int] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None



# Create new router for brands (separate from organisations)
brand_router = APIRouter(prefix="/brands", tags=["brands"])

@brand_router.get("")
async def get_all_brands(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get brands (Filtered by organisation if not superadmin)"""
    # Check if superadmin
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    org_id = current_user.get("organisation_id")

    query = select(Brand)
    if not is_superadmin:
        if not org_id:
            raise HTTPException(status_code=400, detail="Organisation ID not found for user")
        query = query.where(Brand.organisation_id == org_id)
    
    result = await db.execute(query.offset(skip).limit(limit))
    brands = result.scalars().all()
    
    # Get product count for each brand
    brands_with_count = []
    for brand in brands:
        product_result = await db.execute(
            select(func.count(Product.id)).where(Product.brand_id == brand.id)
        )
        product_count = product_result.scalar()
        
        # Get company name if associated
        company_name = None
        if brand.company_id:
            from db.models.company import Company
            company_result = await db.execute(select(Company.name).where(Company.id == brand.company_id))
            company_name = company_result.scalar()

        brands_with_count.append({
            "id": brand.id,
            "name": brand.name,
            "organisation_id": brand.organisation_id,
            "company_id": brand.company_id,
            "company_name": company_name,
            "description": brand.description,
            "logo_url": brand.logo_url,
            "is_active": brand.is_active,
            "created_at": brand.created_at.isoformat() if brand.created_at else None,
            "product_count": product_count
        })
    
    return brands_with_count

@brand_router.get("/{brand_id}")
async def get_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific brand"""
    # Check access
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    org_id = current_user.get("organisation_id")

    query = select(Brand).where(Brand.id == brand_id)
    if not is_superadmin:
        query = query.where(Brand.organisation_id == org_id)

    result = await db.execute(query)
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found or access denied")
    
    return {
        "id": brand.id,
        "name": brand.name,
        "organisation_id": brand.organisation_id,
        "company_id": brand.company_id,
        "description": brand.description,
        "is_active": brand.is_active,
        "created_at": brand.created_at.isoformat() if brand.created_at else None
    }

@brand_router.get("/{brand_id}/products")
async def get_brand_products(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Get all products for a specific brand"""
    # Verify brand exists
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Get products for this brand
    products_result = await db.execute(
        select(Product).where(Product.brand_id == brand_id)
    )
    products = products_result.scalars().all()
    
    return [{
        "id": p.id,
        "brand_id": p.brand_id,
        "name": p.name,
        "category": p.category,
        "sub_category": p.sub_category,
        "description": p.description,
        "target_crops": p.target_crops,
        "target_problems": p.target_problems,
        "dosage": p.dosage,
        "usage_instructions": p.usage_instructions,
        "safety_precautions": p.safety_precautions,
        "price_range": p.price_range,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat() if p.created_at else None
    } for p in products]

@brand_router.post("")
async def create_brand(
    brand: BrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new brand"""
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    org_id = brand.organisation_id if is_superadmin else current_user.get("organisation_id")

    if not org_id:
        raise HTTPException(status_code=400, detail="Organisation ID is required")

    # Verify organisation exists
    org_result = await db.execute(
        select(Organisation).where(Organisation.id == org_id)
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Verify company exists if provided
    if brand.company_id:
        from db.models.company import Company
        company_result = await db.execute(
            select(Company).where(and_(Company.id == brand.company_id, Company.organisation_id == org_id))
        )
        if not company_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invalid company ID for this organisation")

    new_brand = Brand(
        name=brand.name,
        organisation_id=org_id,
        company_id=brand.company_id,
        description=brand.description,
        logo_url=brand.logo_url,
        is_active=brand.is_active
    )
    
    db.add(new_brand)
    await db.commit()
    await db.refresh(new_brand)
    
    return {
        "id": new_brand.id,
        "name": new_brand.name,
        "organisation_id": new_brand.organisation_id,
        "company_id": new_brand.company_id,
        "description": new_brand.description,
        "logo_url": new_brand.logo_url,
        "is_active": new_brand.is_active,
        "created_at": new_brand.created_at.isoformat() if new_brand.created_at else None
    }

@brand_router.put("/{brand_id}")
async def update_brand(
    brand_id: int,
    brand_update: BrandUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a brand"""
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    org_id = current_user.get("organisation_id")

    query = select(Brand).where(Brand.id == brand_id)
    if not is_superadmin:
        query = query.where(Brand.organisation_id == org_id)

    result = await db.execute(query)
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found or access denied")
    
    if brand_update.name is not None:
        brand.name = brand_update.name
    if brand_update.organisation_id is not None:
        brand.organisation_id = brand_update.organisation_id
    if brand_update.company_id is not None:
        # Verify company belongs to same organisation
        from db.models.company import Company
        company_result = await db.execute(
            select(Company).where(and_(Company.id == brand_update.company_id, Company.organisation_id == (brand_update.organisation_id if brand_update.organisation_id else brand.organisation_id)))
        )
        if not company_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Invalid company ID for this organisation")
        brand.company_id = brand_update.company_id
    if brand_update.description is not None:
        brand.description = brand_update.description
    if brand_update.logo_url is not None:
        brand.logo_url = brand_update.logo_url
    if brand_update.is_active is not None:
        brand.is_active = brand_update.is_active
    
    await db.commit()
    await db.refresh(brand)
    
    return {
        "id": brand.id,
        "name": brand.name,
        "organisation_id": brand.organisation_id,
        "company_id": brand.company_id,
        "description": brand.description,
        "logo_url": brand.logo_url,
        "is_active": brand.is_active,
        "created_at": brand.created_at.isoformat() if brand.created_at else None
    }

@brand_router.delete("/{brand_id}")
async def delete_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a brand and all its products"""
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    org_id = current_user.get("organisation_id")

    query = select(Brand).where(Brand.id == brand_id)
    if not is_superadmin:
        query = query.where(Brand.organisation_id == org_id)

    result = await db.execute(query)
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found or access denied")
    
    # Delete all associated products first
    from sqlalchemy import delete as sa_delete
    product_delete = await db.execute(
        sa_delete(Product).where(Product.brand_id == brand_id)
    )
    deleted_products = product_delete.rowcount
    
    await db.delete(brand)
    await db.commit()
    
    return {"message": f"Brand and {deleted_products} associated product(s) deleted successfully"}

@brand_router.get("/organisation/{organisation_id}")
async def get_brands_by_organisation(
    organisation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Get all brands for a specific organisation"""
    result = await db.execute(
        select(Brand).where(Brand.organisation_id == organisation_id)
    )
    brands = result.scalars().all()
    
    return [
        {
            "id": brand.id,
            "name": brand.name,
            "organisation_id": brand.organisation_id,
            "company_id": brand.company_id,
            "description": brand.description,
            "is_active": brand.is_active,
            "created_at": brand.created_at.isoformat() if brand.created_at else None
        }
        for brand in brands
    ]


# ==================== Product Management ====================

# (Product models consolidated at the top)

class ProductResponse(BaseModel):
    id: int
    name: str
    brand_id: int
    description: Optional[str]
    category: Optional[str]
    target_crops: Optional[str]
    target_problems: Optional[str]
    application_method: Optional[str]
    dosage_info: Optional[str]
    is_active: bool
    created_at: str

# Create new router for products
product_router = APIRouter(prefix="/products", tags=["products"])

@product_router.get("")
async def get_all_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get products (Filtered by organisation if not superadmin)"""
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    org_id = current_user.get("organisation_id")

    # If superadmin, see all. If org admin, see only theirs.
    if is_superadmin:
        result = await db.execute(select(Product).offset(skip).limit(limit))
    else:
        if not org_id:
            raise HTTPException(status_code=400, detail="Organisation ID not found for user")
        result = await db.execute(
            select(Product).where(Product.organisation_id == org_id).offset(skip).limit(limit)
        )
    products = result.scalars().all()
    
    # Get brand and company names
    from db.models.company import Company
    
    response_data = []
    for product in products:
        company_name = None
        brand_name = None
        
        if product.company_id:
            co_res = await db.execute(select(Company.name).where(Company.id == product.company_id))
            company_name = co_res.scalar()
            
        if product.brand_id:
            br_res = await db.execute(select(Brand.name).where(Brand.id == product.brand_id))
            brand_name = br_res.scalar()
            
        response_data.append({
            "id": product.id,
            "name": product.name,
            "brand_id": product.brand_id,
            "brand_name": brand_name,
            "organisation_id": product.organisation_id,
            "company_id": product.company_id,
            "company_name": company_name,
            "description": product.description,
            "category": product.category,
            "sub_category": product.sub_category,
            "target_crops": product.target_crops,
            "target_problems": product.target_problems,
            "usage_instructions": product.usage_instructions,
            "dosage": product.dosage,
            "safety_precautions": product.safety_precautions,
            "price_range": product.price_range,
            "is_active": product.is_active,
            "created_at": product.created_at.isoformat() if product.created_at else None
        })
    
    return response_data

@product_router.get("/{product_id}")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific product"""
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    org_id = current_user.get("organisation_id")

    query = select(Product).where(Product.id == product_id)
    if not is_superadmin:
        query = query.where(Product.organisation_id == org_id)

    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or access denied")
    
    company_name = None
    brand_name = None
    if product.company_id:
        from db.models.company import Company
        co_res = await db.execute(select(Company.name).where(Company.id == product.company_id))
        company_name = co_res.scalar()
    
    if product.brand_id:
        br_res = await db.execute(select(Brand.name).where(Brand.id == product.brand_id))
        brand_name = br_res.scalar()

    return {
        "id": product.id,
        "name": product.name,
        "brand_id": product.brand_id,
        "brand_name": brand_name,
        "organisation_id": product.organisation_id,
        "company_id": product.company_id,
        "company_name": company_name,
        "description": product.description,
        "category": product.category,
        "target_crops": product.target_crops,
        "target_problems": product.target_problems,
        "usage_instructions": product.usage_instructions,
        "dosage": product.dosage,
        "safety_precautions": product.safety_precautions,
        "price_range": product.price_range,
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat() if product.created_at else None
    }

@product_router.post("")
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new product"""
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    org_id = current_user.get("organisation_id")

    # Verify company exists
    from db.models.company import Company
    company_result = await db.execute(
        select(Company).where(Company.id == product.company_id)
    )
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    if not is_superadmin and company.organisation_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied to this company")

    brand = None
    if product.brand_id:
        brand_result = await db.execute(
            select(Brand).where(Brand.id == product.brand_id)
        )
        brand = brand_result.scalar_one_or_none()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")

    # Check for duplicate product by name in the same company
    existing_product_result = await db.execute(
        select(Product).where(
            and_(
                func.lower(Product.name) == product.name.lower().strip(),
                Product.company_id == product.company_id
            )
        )
    )
    if existing_product_result.scalars().first():
        raise HTTPException(status_code=400, detail="A product with this name already exists in this company")

    new_product = Product(
        name=product.name,
        company_id=product.company_id,
        organisation_id=company.organisation_id,
        brand_id=product.brand_id,
        description=product.description,
        category=product.category or "other",
        sub_category=product.sub_category,
        target_crops=product.target_crops,
        target_problems=product.target_problems,
        dosage=product.dosage,
        usage_instructions=product.usage_instructions,
        safety_precautions=product.safety_precautions,
        price_range=product.price_range,
        is_active=product.is_active
    )
    
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    brand_name = brand.name if brand else None
    company_name = company.name

    return {
        "id": new_product.id,
        "name": new_product.name,
        "brand_id": new_product.brand_id,
        "brand_name": brand_name,
        "organisation_id": new_product.organisation_id,
        "company_id": new_product.company_id,
        "company_name": company_name,
        "description": new_product.description,
        "category": new_product.category,
        "sub_category": new_product.sub_category,
        "target_crops": new_product.target_crops,
        "target_problems": new_product.target_problems,
        "usage_instructions": new_product.usage_instructions,
        "dosage": new_product.dosage,
        "is_active": new_product.is_active,
        "created_at": new_product.created_at.isoformat() if new_product.created_at else None
    }

@product_router.put("/{product_id}")
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a product"""
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    org_id = current_user.get("organisation_id")

    query = select(Product).where(Product.id == product_id)
    if not is_superadmin:
        query = query.where(Product.organisation_id == org_id)

    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or access denied")
    
    if product_update.name is not None:
        product.name = product_update.name
    if product_update.company_id is not None:
        from db.models.company import Company
        co_res = await db.execute(select(Company).where(Company.id == product_update.company_id))
        company = co_res.scalar_one_or_none()
        if not company or (not is_superadmin and company.organisation_id != org_id):
            raise HTTPException(status_code=400, detail="Invalid company for this organisation")
        product.company_id = product_update.company_id
        product.organisation_id = company.organisation_id
    if product_update.brand_id is not None:
        # Verify brand exists and belongs to same org
        brand_res = await db.execute(select(Brand).where(Brand.id == product_update.brand_id))
        brand = brand_res.scalar_one_or_none()
        if not brand or brand.organisation_id != product.organisation_id:
            raise HTTPException(status_code=400, detail="Invalid brand for this organisation")
        product.brand_id = product_update.brand_id
    if product_update.category is not None:
        product.category = product_update.category
    if product_update.sub_category is not None:
        product.sub_category = product_update.sub_category
    if product_update.description is not None:
        product.description = product_update.description
    if product_update.target_crops is not None:
        product.target_crops = product_update.target_crops
    if product_update.target_problems is not None:
        product.target_problems = product_update.target_problems
    if product_update.dosage is not None:
        product.dosage = product_update.dosage
    if product_update.usage_instructions is not None:
        product.usage_instructions = product_update.usage_instructions
    if product_update.safety_precautions is not None:
        product.safety_precautions = product_update.safety_precautions
    if product_update.price_range is not None:
        product.price_range = product_update.price_range
    if product_update.is_active is not None:
        product.is_active = product_update.is_active
    
    await db.commit()
    await db.refresh(product)
    
    # Get names for response
    company_name = None
    brand_name = None
    if product.company_id:
        from db.models.company import Company
        co_res = await db.execute(select(Company.name).where(Company.id == product.company_id))
        company_name = co_res.scalar()
    
    if product.brand_id:
        br_res = await db.execute(select(Brand.name).where(Brand.id == product.brand_id))
        brand_name = br_res.scalar()

    return {
        "id": product.id,
        "name": product.name,
        "brand_id": product.brand_id,
        "brand_name": brand_name,
        "organisation_id": product.organisation_id,
        "company_id": product.company_id,
        "company_name": company_name,
        "description": product.description,
        "category": product.category,
        "sub_category": product.sub_category,
        "target_crops": product.target_crops,
        "target_problems": product.target_problems,
        "usage_instructions": product.usage_instructions,
        "dosage": product.dosage,
        "safety_precautions": product.safety_precautions,
        "price_range": product.price_range,
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat() if product.created_at else None
    }

@product_router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a product"""
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    org_id = current_user.get("organisation_id")

    query = select(Product).where(Product.id == product_id)
    if not is_superadmin:
        query = query.where(Product.organisation_id == org_id)

    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or access denied")
    
    await db.delete(product)
    await db.commit()
    
    return {"message": "Product deleted successfully"}

@product_router.get("/brand/{brand_id}")
async def get_products_by_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Get all products for a specific brand"""
    result = await db.execute(
        select(Product).where(Product.brand_id == brand_id)
    )
    products = result.scalars().all()
    
    return [
        {
            "id": product.id,
            "name": product.name,
            "brand_id": product.brand_id,
            "description": product.description,
            "category": product.category,
            "target_crops": product.target_crops,
            "target_problems": product.target_problems,
            "application_method": product.usage_instructions,
            "dosage_info": product.dosage,
            "is_active": product.is_active,
            "created_at": product.created_at.isoformat() if product.created_at else None
        }
        for product in products
    ]

@product_router.get("/organisation/{organisation_id}")
async def get_products_by_organisation(
    organisation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Get all products for a specific organisation"""
    # Get all brands for this organisation
    brand_result = await db.execute(
        select(Brand.id).where(Brand.organisation_id == organisation_id)
    )
    brand_ids = [row[0] for row in brand_result.all()]
    
    if not brand_ids:
        return []
    
    # Get all products for these brands
    result = await db.execute(
        select(Product).where(Product.brand_id.in_(brand_ids))
    )
    products = result.scalars().all()
    
    return [
        {
            "id": product.id,
            "name": product.name,
            "brand_id": product.brand_id,
            "description": product.description,
            "category": product.category,
            "target_crops": product.target_crops,
            "target_problems": product.target_problems,
            "application_method": product.usage_instructions,
            "dosage_info": product.dosage,
            "is_active": product.is_active,
            "created_at": product.created_at.isoformat() if product.created_at else None
        }
        for product in products
    ]


@product_router.get("/import/template/{type}")
async def get_product_import_template(
    type: str,
    current_user = Depends(get_current_user)
):
    """
    Download product import template (CSV or Excel)
    """
    headers = [
        "name", "brand_name", "category", "sub_category", "description", 
        "target_crops", "target_problems", "dosage", "usage_instructions", 
        "safety_precautions", "price_range", "is_active"
    ]
    
    if type == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        # Add a sample row
        writer.writerow([
            "Sample Product", "Sample Brand", "Seeds", "Hybrid", "High yield seeds", 
            "Cotton, Wheat", "Pest attack", "2kg/acre", "Sow at 2 inch depth", 
            "Keep away from children", "500-1000", "true"
        ])
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=products_template.csv"}
        )
    elif type == "excel":
        if not openpyxl:
            raise HTTPException(status_code=400, detail="Excel support not available.")
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(headers)
        ws.append([
            "Sample Product", "Sample Brand", "Seeds", "Hybrid", "High yield seeds", 
            "Cotton, Wheat", "Pest attack", "2kg/acre", "Sow at 2 inch depth", 
            "Keep away from children", "500-1000", "true"
        ])
        
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=products_template.xlsx"}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid template type. Use 'csv' or 'excel'.")

@product_router.post("/upload-csv")
async def upload_products_csv(
    file: UploadFile = File(...),
    company_id: int = Form(...),
    brand_id: Optional[int] = Form(None),
    brand_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Upload products via CSV or Excel file
    Supports providing company_id, brand_id OR brand_name (default for all rows) 
    OR per-row brand_name in the file.
    """
    is_superadmin = current_user.get("role") in ["admin", "superadmin"]
    user_org_id = current_user.get("organisation_id")
    
    logger.info(f"🔍 Product CSV Upload - File: {file.filename}, Company ID: {company_id}, Brand ID: {brand_id}, Brand Name: {brand_name}")
    
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload CSV or Excel file.")
    
    # Verify company
    from db.models.company import Company
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    target_company = company_result.scalar_one_or_none()
    if not target_company:
        raise HTTPException(status_code=404, detail="Company not found")
    if not is_superadmin and target_company.organisation_id != user_org_id:
        raise HTTPException(status_code=403, detail="Access denied to this company")
    
    # Initial brand check if brand_id is provided
    default_brand = None
    if brand_id:
        brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
        default_brand = brand_result.scalar_one_or_none()
        if not default_brand:
            raise HTTPException(status_code=404, detail=f"Brand ID {brand_id} not found")
        # Check ownership
        if not is_superadmin and default_brand.organisation_id != user_org_id:
            raise HTTPException(status_code=403, detail="Access denied to this brand")
    
    # helper to get or create brand
    async def get_or_create_brand(name_to_use, org_id, co_id):
        if not name_to_use or not org_id: return None
        # Check existing
        brand_res = await db.execute(
            select(Brand).where(and_(Brand.name == name_to_use, Brand.organisation_id == org_id, Brand.company_id == co_id))
        )
        existing_brand = brand_res.scalars().first()
        if existing_brand:
            return existing_brand
        
        # Create new
        new_b = Brand(name=name_to_use, organisation_id=org_id, company_id=co_id, is_active=True)
        db.add(new_b)
        await db.flush() # Get ID without committing
        return new_b

    # Determine default brand from name if provided and ID is not
    effective_org_id = target_company.organisation_id
    if not default_brand and brand_name and effective_org_id:
        default_brand = await get_or_create_brand(brand_name, effective_org_id, company_id)

    success_count = 0
    errors = []
    brand_cache = {} # cache brand objects to avoid redundant DB hits
    if default_brand:
        brand_cache[default_brand.name] = default_brand
    
    try:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            csv_data = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            rows = list(csv_reader)
            logger.info(f"📄 Parsed CSV - Total rows: {len(rows)}")
        else:
            if not openpyxl:
                raise HTTPException(status_code=400, detail="Excel support not available.")
            workbook = openpyxl.load_workbook(io.BytesIO(content))
            sheet = workbook.active
            headers = [cell.value for cell in sheet[1]]
            rows = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if any(row):
                    rows.append(dict(zip(headers, row)))
            logger.info(f"📄 Parsed Excel - Total rows: {len(rows)}")
        
        if rows:
            logger.info(f"📋 CSV Headers: {list(rows[0].keys())}")
            logger.info(f"📋 First row data: {rows[0]}")
        
        for idx, row in enumerate(rows, start=2):
            try:
                if not row.get('name'):
                    logger.warning(f"⚠️ Row {idx}: Skipping - missing name. Row: {row}")
                    continue
                
                # Determine brand for this specific row
                row_brand_name = row.get('brand_name') or brand_name
                current_row_brand = default_brand
                
                if row_brand_name and effective_org_id:
                    if row_brand_name in brand_cache:
                        current_row_brand = brand_cache[row_brand_name]
                    else:
                        current_row_brand = await get_or_create_brand(row_brand_name, effective_org_id, company_id)
                        brand_cache[row_brand_name] = current_row_brand

                if not current_row_brand:
                    # Fallback to organisation level if no brand info
                    target_org_id = effective_org_id
                    target_brand_id = None
                    target_company_id = company_id
                else:
                    target_org_id = current_row_brand.organisation_id
                    target_brand_id = current_row_brand.id
                    target_company_id = company_id

                if not target_org_id:
                    error_msg = f"Row {idx}: Missing organisation context"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
                    continue

                logger.info(f"✅ Row {idx}: Creating product '{row.get('name')}' for brand {target_brand_id}")
                
                product_name = str(row.get('name', '')).strip()
                
                # Check for duplicate product
                existing_product = await db.execute(
                    select(Product).where(
                        and_(
                            func.lower(Product.name) == product_name.lower(),
                            Product.company_id == target_company_id
                        )
                    )
                )
                if existing_product.scalars().first():
                    error_msg = f"Row {idx}: Product '{product_name}' already exists in this company"
                    logger.warning(f"⏭️ {error_msg}")
                    errors.append(error_msg)
                    continue
                
                product = Product(
                    organisation_id=target_org_id,
                    company_id=target_company_id,
                    brand_id=target_brand_id,
                    name=product_name,
                    category=str(row.get('category', 'other')).strip(),
                    sub_category=str(row.get('sub_category', '')).strip() if row.get('sub_category') else None,
                    description=str(row.get('description', '')).strip() if row.get('description') else None,
                    target_crops=str(row.get('target_crops', '')).strip() if row.get('target_crops') else None,
                    target_problems=str(row.get('target_problems', '')).strip() if row.get('target_problems') else None,
                    dosage=str(row.get('dosage', '')).strip() if row.get('dosage') else None,
                    usage_instructions=str(row.get('usage_instructions', '')).strip() if row.get('usage_instructions') else None,
                    safety_precautions=str(row.get('safety_precautions', '')).strip() if row.get('safety_precautions') else None,
                    price_range=str(row.get('price_range', '')).strip() if row.get('price_range') else None,
                    is_active=str(row.get('is_active', 'true')).lower() in ('true', '1', 'yes'),
                    created_at=datetime.now(timezone.utc)
                )
                
                db.add(product)
                success_count += 1
                logger.info(f"✅ Row {idx}: Product added to session")
                
            except Exception as e:
                error_msg = f"Row {idx}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                errors.append(error_msg)
        
        logger.info(f"📊 CSV Processing Complete - Success: {success_count}, Errors: {len(errors)}")
        
        if success_count > 0:
            logger.info(f"💾 Committing {success_count} products to database...")
            await db.commit()
            logger.info(f"✅ Database commit successful!")
        else:
            logger.warning(f"⚠️ No products to commit")
        
        return {
            "message": f"CSV processed successfully. {success_count} products added to brand '{default_brand.name if default_brand else 'multiple brands'}'",
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors[:10]
        }
        
    except Exception as e:
        logger.error(f"❌ CSV Upload Failed: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")
