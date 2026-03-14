from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response, BackgroundTasks
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
    status: str = Field(default="active", pattern="^(active|inactive|rejected|pending)$")
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
    status: Optional[str] = Field(None, pattern="^(active|inactive|rejected|pending)$")
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
    company_name: Optional[str] = None
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
    
    brand_responses = []
    from db.models.company import Company
    
    for brand in brands:
        company_name = None
        if brand.company_id:
            company_result = await db.execute(select(Company.name).where(Company.id == brand.company_id))
            company_name = company_result.scalar()
            
        brand_responses.append(BrandResponse(
            id=brand.id,
            name=brand.name,
            organisation_id=brand.organisation_id,
            company_id=brand.company_id,
            company_name=company_name,
            description=brand.description,
            logo_url=brand.logo_url,
            is_active=brand.is_active,
            created_at=brand.created_at.isoformat() if brand.created_at else "",
            product_count=0 # Placeholder, can be calculated if needed
        ))
    
    return brand_responses

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


