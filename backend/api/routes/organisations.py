from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.session import get_db
from db.models.organisation import Organisation
from db.models.organisation_phone import OrganisationPhoneNumber
from db.models.brand import Brand
from db.models.product import Product
from core.auth import get_current_super_admin
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
    domain: Optional[str] = Field(None, max_length=200)
    status: str = Field(default="active", pattern="^(active|inactive|suspended)$")
    plan_type: str = Field(default="basic", pattern="^(basic|professional|enterprise)$")

class OrganisationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    domain: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")
    plan_type: Optional[str] = Field(None, pattern="^(basic|professional|enterprise)$")

class OrganisationResponse(BaseModel):
    id: int
    name: str
    domain: Optional[str]
    status: str
    plan_type: str
    phone_numbers: Optional[List[str]]
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
    company_id: Optional[int] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None

class BrandResponse(BaseModel):
    id: int
    organisation_id: int
    company_id: Optional[int]
    name: str
    description: Optional[str]
    logo_url: Optional[str]
    is_active: bool
    created_at: str

class ProductCreate(BaseModel):
    brand_id: Optional[int] = None
    name: str = Field(..., min_length=2, max_length=200)
    category: str
    sub_category: Optional[str] = None
    description: Optional[str] = None
    target_crops: Optional[List[str]] = None
    target_problems: Optional[List[str]] = None
    dosage: Optional[str] = None
    usage_instructions: Optional[str] = None
    safety_precautions: Optional[str] = None
    price_range: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    organisation_id: int
    brand_id: Optional[int]
    name: str
    category: str
    sub_category: Optional[str]
    description: Optional[str]
    target_crops: Optional[List[str]]
    target_problems: Optional[List[str]]
    dosage: Optional[str]
    usage_instructions: Optional[str]
    safety_precautions: Optional[str]
    price_range: Optional[str]
    is_active: bool
    created_at: str

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
            domain=org.domain,
            status=org.status,
            plan_type=org.plan_type,
            phone_numbers=json.loads(org.phone_numbers) if org.phone_numbers else None,
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
        domain=org.domain,
        status=org.status,
        plan_type=org.plan_type,
        phone_numbers=json.loads(org.phone_numbers) if org.phone_numbers else None,
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
    # Check if domain already exists
    if org_data.domain:
        result = await db.execute(
            select(Organisation).where(Organisation.domain == org_data.domain)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Domain already exists")
    
    new_org = Organisation(
        name=org_data.name,
        domain=org_data.domain,
        status=org_data.status,
        plan_type=org_data.plan_type
    )
    
    db.add(new_org)
    await db.commit()
    await db.refresh(new_org)
    
    logger.info(f"Super Admin {current_user['username']} created organisation: {new_org.name}")
    
    return OrganisationResponse(
        id=new_org.id,
        name=new_org.name,
        domain=new_org.domain,
        status=new_org.status,
        plan_type=new_org.plan_type,
        phone_numbers=None,
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
    
    # Check domain uniqueness if being changed
    if org_data.domain and org_data.domain != org.domain:
        result = await db.execute(
            select(Organisation).where(Organisation.domain == org_data.domain)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Domain already in use")
        org.domain = org_data.domain
    
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
        domain=org.domain,
        status=org.status,
        plan_type=org.plan_type,
        phone_numbers=json.loads(org.phone_numbers) if org.phone_numbers else None,
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
            organisation_id=brand.organisation_id,
            name=brand.name,
            description=brand.description,
            logo_url=brand.logo_url,
            is_active=brand.is_active,
            created_at=brand.created_at.isoformat() if brand.created_at else ""
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
        organisation_id=new_brand.organisation_id,
        company_id=new_brand.company_id,
        name=new_brand.name,
        description=new_brand.description,
        logo_url=new_brand.logo_url,
        is_active=new_brand.is_active,
        created_at=new_brand.created_at.isoformat() if new_brand.created_at else ""
    )

# ==================== Product Management ====================

@router.get("/{org_id}/products", response_model=List[ProductResponse])
async def get_organisation_products(
    org_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Get all products for an organisation"""
    result = await db.execute(
        select(Product).where(Product.organisation_id == org_id).offset(skip).limit(limit)
    )
    products = result.scalars().all()
    
    return [
        ProductResponse(
            id=prod.id,
            organisation_id=prod.organisation_id,
            brand_id=prod.brand_id,
            name=prod.name,
            category=prod.category,
            sub_category=prod.sub_category,
            description=prod.description,
            target_crops=json.loads(prod.target_crops) if prod.target_crops else None,
            target_problems=json.loads(prod.target_problems) if prod.target_problems else None,
            dosage=prod.dosage,
            usage_instructions=prod.usage_instructions,
            safety_precautions=prod.safety_precautions,
            price_range=prod.price_range,
            is_active=prod.is_active,
            created_at=prod.created_at.isoformat() if prod.created_at else ""
        )
        for prod in products
    ]

@router.post("/{org_id}/products", response_model=ProductResponse)
async def create_product(
    org_id: int,
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """Create product for organisation"""
    new_product = Product(
        organisation_id=org_id,
        brand_id=product_data.brand_id,
        name=product_data.name,
        category=product_data.category,
        sub_category=product_data.sub_category,
        description=product_data.description,
        target_crops=json.dumps(product_data.target_crops) if product_data.target_crops else None,
        target_problems=json.dumps(product_data.target_problems) if product_data.target_problems else None,
        dosage=product_data.dosage,
        usage_instructions=product_data.usage_instructions,
        safety_precautions=product_data.safety_precautions,
        price_range=product_data.price_range,
        is_active=True
    )
    
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    logger.info(f"Created product {product_data.name} for org {org_id}")
    
    return ProductResponse(
        id=new_product.id,
        organisation_id=new_product.organisation_id,
        brand_id=new_product.brand_id,
        name=new_product.name,
        category=new_product.category,
        sub_category=new_product.sub_category,
        description=new_product.description,
        target_crops=product_data.target_crops,
        target_problems=product_data.target_problems,
        dosage=new_product.dosage,
        usage_instructions=new_product.usage_instructions,
        safety_precautions=new_product.safety_precautions,
        price_range=new_product.price_range,
        is_active=new_product.is_active,
        created_at=new_product.created_at.isoformat() if new_product.created_at else ""
    )

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

class BrandCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    organisation_id: int
    company_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True

class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    company_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class BrandResponse(BaseModel):
    id: int
    name: str
    organisation_id: int
    company_id: Optional[int]
    description: Optional[str]
    logo_url: Optional[str] = None
    is_active: bool
    created_at: str
    product_count: Optional[int] = 0

# Create new router for brands (separate from organisations)
brand_router = APIRouter(prefix="/brands", tags=["brands"])

@brand_router.get("")
async def get_all_brands(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Get all brands (super admin only)"""
    result = await db.execute(
        select(Brand).offset(skip).limit(limit)
    )
    brands = result.scalars().all()
    
    # Get product count for each brand
    brands_with_count = []
    for brand in brands:
        product_result = await db.execute(
            select(func.count(Product.id)).where(Product.brand_id == brand.id)
        )
        product_count = product_result.scalar()
        
        brands_with_count.append({
            "id": brand.id,
            "name": brand.name,
            "organisation_id": brand.organisation_id,
            "company_id": brand.company_id,
            "description": brand.description,
            "is_active": brand.is_active,
            "created_at": brand.created_at.isoformat() if brand.created_at else None,
            "product_count": product_count
        })
    
    return brands_with_count

@brand_router.get("/{brand_id}")
async def get_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Get a specific brand"""
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
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
    current_user = Depends(get_current_super_admin)
):
    """Create a new brand"""
    # Verify organisation exists
    org_result = await db.execute(
        select(Organisation).where(Organisation.id == brand.organisation_id)
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    new_brand = Brand(
        name=brand.name,
        organisation_id=brand.organisation_id,
        company_id=brand.company_id,
        description=brand.description,
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
        "is_active": new_brand.is_active,
        "created_at": new_brand.created_at.isoformat() if new_brand.created_at else None
    }

@brand_router.put("/{brand_id}")
async def update_brand(
    brand_id: int,
    brand_update: BrandUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Update a brand"""
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    if brand_update.name is not None:
        brand.name = brand_update.name
    if brand_update.company_id is not None:
        brand.company_id = brand_update.company_id
    if brand_update.description is not None:
        brand.description = brand_update.description
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
        "is_active": brand.is_active,
        "created_at": brand.created_at.isoformat() if brand.created_at else None
    }

@brand_router.delete("/{brand_id}")
async def delete_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Delete a brand and all its products"""
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Delete associated products first
    await db.execute(select(Product).where(Product.brand_id == brand_id))
    
    await db.delete(brand)
    await db.commit()
    
    return {"message": "Brand deleted successfully"}

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

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    brand_id: int
    description: Optional[str] = None
    category: Optional[str] = None
    target_crops: Optional[str] = None
    target_problems: Optional[str] = None
    application_method: Optional[str] = None
    dosage_info: Optional[str] = None
    is_active: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    target_crops: Optional[str] = None
    target_problems: Optional[str] = None
    application_method: Optional[str] = None
    dosage_info: Optional[str] = None
    is_active: Optional[bool] = None

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
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Get all products (super admin only)"""
    result = await db.execute(
        select(Product).offset(skip).limit(limit)
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

@product_router.get("/{product_id}")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Get a specific product"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
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

@product_router.post("")
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Create a new product"""
    # Verify brand exists and get its organisation_id and company_id
    brand_result = await db.execute(
        select(Brand).where(Brand.id == product.brand_id)
    )
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    new_product = Product(
        name=product.name,
        brand_id=product.brand_id,
        organisation_id=brand.organisation_id,
        company_id=brand.company_id,
        description=product.description,
        category=product.category or "other",
        target_crops=product.target_crops,
        target_problems=product.target_problems,
        dosage=product.dosage_info,
        usage_instructions=product.application_method,
        is_active=product.is_active
    )
    
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    return {
        "id": new_product.id,
        "name": new_product.name,
        "brand_id": new_product.brand_id,
        "organisation_id": new_product.organisation_id,
        "company_id": new_product.company_id,
        "description": new_product.description,
        "category": new_product.category,
        "target_crops": new_product.target_crops,
        "target_problems": new_product.target_problems,
        "application_method": new_product.usage_instructions,
        "dosage_info": new_product.dosage,
        "is_active": new_product.is_active,
        "created_at": new_product.created_at.isoformat() if new_product.created_at else None
    }

@product_router.put("/{product_id}")
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Update a product"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product_update.name is not None:
        product.name = product_update.name
    if product_update.description is not None:
        product.description = product_update.description
    if product_update.category is not None:
        product.category = product_update.category
    if product_update.target_crops is not None:
        product.target_crops = product_update.target_crops
    if product_update.target_problems is not None:
        product.target_problems = product_update.target_problems
    if product_update.application_method is not None:
        product.usage_instructions = product_update.application_method
    if product_update.dosage_info is not None:
        product.dosage = product_update.dosage_info
    if product_update.is_active is not None:
        product.is_active = product_update.is_active
    
    await db.commit()
    await db.refresh(product)
    
    return {
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

@product_router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """Delete a product"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
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


@product_router.post("/upload-csv")
async def upload_products_csv(
    file: UploadFile = File(...),
    brand_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_super_admin)
):
    """
    Upload products via CSV or Excel file (Super Admin only)
    All products will be associated with the specified brand_id
    Expected columns: name, category, description, target_crops, 
                     target_problems, dosage, usage_instructions, is_active
    """
    
    logger.info(f"🔍 Admin CSV Upload - File: {file.filename}, Brand ID: {brand_id}")
    
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload CSV or Excel file.")
    
    # Verify brand exists and get its organisation_id and company_id
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand ID {brand_id} not found")
    
    logger.info(f"✅ Brand found: {brand.name} (org={brand.organisation_id}, company={brand.company_id})")
    
    success_count = 0
    errors = []
    
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
                
                logger.info(f"✅ Row {idx}: Creating product '{row.get('name')}'")
                
                product = Product(
                    organisation_id=brand.organisation_id,
                    company_id=brand.company_id,
                    brand_id=brand_id,
                    name=str(row.get('name', '')).strip(),
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
            "message": f"CSV processed successfully. {success_count} products added to brand '{brand.name}'",
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors[:10]
        }
        
    except Exception as e:
        logger.error(f"❌ CSV Upload Failed: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")
