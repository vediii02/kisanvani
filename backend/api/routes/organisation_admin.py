"""
Organisation Admin Routes
Each organisation can manage their own data through their dedicated dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import csv
import io
import openpyxl
from datetime import datetime, timezone

from core.dependencies import get_current_organisation_admin
from db.session import get_db
from db.models.user import User
from db.models.organisation import Organisation
from db.models.brand import Brand
from db.models.product import Product
from schemas.product import ProductCreate, ProductUpdate, ProductResponse
from pydantic import BaseModel
from core.auth import get_password_hash, verify_password

router = APIRouter()


# Schema for password update
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


# Schema for organisation profile update
class OrganisationProfileUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class OrganisationProfile(BaseModel):
    id: int
    name: str
    domain: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    description: Optional[str]
    is_active: bool
    is_enterprise: bool
    created_at: str
    
    class Config:
        from_attributes = True


class BrandBase(BaseModel):
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool = True


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class BrandResponse(BrandBase):
    id: int
    organisation_id: int
    created_at: str
    
    class Config:
        from_attributes = True


# Dashboard Stats
class DashboardStats(BaseModel):
    total_brands: int
    total_products: int
    active_products: int
    categories: int
    recent_products: List[ProductResponse]


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get organisation dashboard statistics"""
    org_id = current_user.organisation_id
    
    # Count brands
    brands_result = await db.execute(
        select(func.count(Brand.id)).where(Brand.organisation_id == org_id)
    )
    total_brands = brands_result.scalar() or 0
    
    # Count products
    products_result = await db.execute(
        select(func.count(Product.id)).where(Product.organisation_id == org_id)
    )
    total_products = products_result.scalar() or 0
    
    # Count active products
    active_result = await db.execute(
        select(func.count(Product.id)).where(
            Product.organisation_id == org_id,
            Product.is_active == True
        )
    )
    active_products = active_result.scalar() or 0
    
    # Count categories
    categories_result = await db.execute(
        select(func.count(func.distinct(Product.category))).where(
            Product.organisation_id == org_id
        )
    )
    categories = categories_result.scalar() or 0
    
    # Get recent products
    recent_result = await db.execute(
        select(Product)
        .where(Product.organisation_id == org_id)
        .order_by(Product.created_at.desc())
        .limit(5)
    )
    recent_products = recent_result.scalars().all()
    
    return {
        "total_brands": total_brands,
        "total_products": total_products,
        "active_products": active_products,
        "categories": categories,
        "recent_products": [ProductResponse.from_orm(p) for p in recent_products]
    }


# Password Update
@router.patch("/profile/password", status_code=status.HTTP_200_OK)
async def update_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the current user's password
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


# Organisation Profile Management
@router.get("/profile", response_model=OrganisationProfile)
async def get_organisation_profile(
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get organisation profile"""
    result = await db.execute(
        select(Organisation).where(Organisation.id == current_user.organisation_id)
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    return OrganisationProfile(
        id=org.id,
        name=org.name,
        domain=org.domain,
        phone=org.phone,
        email=org.email,
        description=org.description,
        is_active=org.is_active,
        is_enterprise=org.is_enterprise,
        created_at=org.created_at.isoformat() if org.created_at else ""
    )


@router.put("/profile", response_model=OrganisationProfile)
async def update_organisation_profile(
    profile_update: OrganisationProfileUpdate,
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update organisation profile"""
    result = await db.execute(
        select(Organisation).where(Organisation.id == current_user.organisation_id)
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Update fields
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)
    
    await db.commit()
    await db.refresh(org)
    
    return OrganisationProfile(
        id=org.id,
        name=org.name,
        domain=org.domain,
        phone=org.phone,
        email=org.email,
        description=org.description,
        is_active=org.is_active,
        is_enterprise=org.is_enterprise,
        created_at=org.created_at.isoformat() if org.created_at else ""
    )


# Brand Management
@router.get("/brands", response_model=List[BrandResponse])
async def get_organisation_brands(
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all brands for organisation"""
    result = await db.execute(
        select(Brand)
        .where(Brand.organisation_id == current_user.organisation_id)
        .order_by(Brand.name)
    )
    brands = result.scalars().all()
    
    return [
        BrandResponse(
            id=b.id,
            name=b.name,
            description=b.description,
            logo_url=b.logo_url,
            organisation_id=b.organisation_id,
            is_active=b.is_active,
            created_at=b.created_at.isoformat() if b.created_at else ""
        )
        for b in brands
    ]


@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand: BrandCreate,
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create new brand"""
    new_brand = Brand(
        organisation_id=current_user.organisation_id,
        name=brand.name,
        description=brand.description,
        logo_url=brand.logo_url,
        is_active=brand.is_active
    )
    
    db.add(new_brand)
    await db.commit()
    await db.refresh(new_brand)
    
    return BrandResponse(
        id=new_brand.id,
        name=new_brand.name,
        description=new_brand.description,
        logo_url=new_brand.logo_url,
        organisation_id=new_brand.organisation_id,
        is_active=new_brand.is_active,
        created_at=new_brand.created_at.isoformat() if new_brand.created_at else ""
    )


@router.put("/brands/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: int,
    brand_update: BrandUpdate,
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update brand"""
    result = await db.execute(
        select(Brand).where(
            Brand.id == brand_id,
            Brand.organisation_id == current_user.organisation_id
        )
    )
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Update fields
    update_data = brand_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand, field, value)
    
    await db.commit()
    await db.refresh(brand)
    
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        description=brand.description,
        logo_url=brand.logo_url,
        organisation_id=brand.organisation_id,
        is_active=brand.is_active,
        created_at=brand.created_at.isoformat() if brand.created_at else ""
    )


@router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: int,
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete brand"""
    result = await db.execute(
        select(Brand).where(
            Brand.id == brand_id,
            Brand.organisation_id == current_user.organisation_id
        )
    )
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    await db.delete(brand)
    await db.commit()
    
    return None


# Product Management
@router.get("/products", response_model=List[ProductResponse])
async def get_organisation_products(
    skip: int = 0,
    limit: int = 100,
    brand_id: Optional[int] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all products for organisation"""
    query = select(Product).where(Product.organisation_id == current_user.organisation_id)
    
    if brand_id:
        query = query.where(Product.brand_id == brand_id)
    if category:
        query = query.where(Product.category == category)
    if is_active is not None:
        query = query.where(Product.is_active == is_active)
    
    query = query.order_by(Product.name).offset(skip).limit(limit)
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    return [ProductResponse.from_orm(p) for p in products]


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create new product"""
    # Verify brand belongs to organisation
    brand_result = await db.execute(
        select(Brand).where(
            Brand.id == product.brand_id,
            Brand.organisation_id == current_user.organisation_id
        )
    )
    brand = brand_result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=400, detail="Invalid brand_id for your organisation")
    
    new_product = Product(
        organisation_id=current_user.organisation_id,
        **product.dict()
    )
    
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    return ProductResponse.from_orm(new_product)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update product"""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.organisation_id == current_user.organisation_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # If brand_id is being updated, verify it belongs to organisation
    if product_update.brand_id:
        brand_result = await db.execute(
            select(Brand).where(
                Brand.id == product_update.brand_id,
                Brand.organisation_id == current_user.organisation_id
            )
        )
        brand = brand_result.scalar_one_or_none()
        
        if not brand:
            raise HTTPException(status_code=400, detail="Invalid brand_id for your organisation")
    
    # Update fields
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    
    return ProductResponse.from_orm(product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete product"""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.organisation_id == current_user.organisation_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.delete(product)
    await db.commit()
    
    return None


# ============================================================================
# Products CSV/Excel Upload Endpoint
# ============================================================================

@router.post("/products/upload-csv")
async def upload_products_csv(
    file: UploadFile = File(...),
    brand_id: int = Form(...),
    current_user: User = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload products via CSV or Excel file
    All products will be associated with the specified brand_id
    Expected columns: name, category, sub_category, description, 
                     target_crops, target_problems, dosage, usage_instructions, 
                     safety_precautions, price_range, is_active
    """
    
    print(f"🔍 Upload CSV Request - File: {file.filename}, Brand ID: {brand_id}, User: {current_user.email}")
    
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload CSV or Excel file."
        )
    
    # Verify brand exists and belongs to user's organisation
    brand_result = await db.execute(
        select(Brand).where(
            Brand.id == brand_id,
            Brand.organisation_id == current_user.organisation_id
        )
    )
    brand = brand_result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(
            status_code=404,
            detail="Brand not found or doesn't belong to your organisation"
        )
    
    success_count = 0
    error_count = 0
    errors = []
    
    try:
        content = await file.read()
        
        # Parse file based on extension
        if file.filename.endswith('.csv'):
            # Parse CSV
            csv_data = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            rows = list(csv_reader)
            print(f"📄 Parsed CSV - Total rows: {len(rows)}")
            if rows:
                print(f"📋 CSV Headers: {list(rows[0].keys())}")
                print(f"📋 First row data: {rows[0]}")
        else:
            # Parse Excel
            workbook = openpyxl.load_workbook(io.BytesIO(content))
            sheet = workbook.active
            headers = [cell.value for cell in sheet[1]]
            rows = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if any(row):  # Skip empty rows
                    rows.append(dict(zip(headers, row)))
            print(f"📄 Parsed Excel - Total rows: {len(rows)}")
            if rows:
                print(f"📋 Excel Headers: {list(rows[0].keys())}")
        
        # Process each row
        for idx, row in enumerate(rows, start=2):
            try:
                # Skip empty rows
                if not row.get('name'):
                    print(f"⚠️ Row {idx}: Skipping - no 'name' field. Row data: {row}")
                    continue
                
                print(f"✅ Row {idx}: Processing product '{row.get('name')}'")
                
                # Create product with selected brand_id
                product = Product(
                    organisation_id=current_user.organisation_id,
                    brand_id=brand_id,  # Use the brand_id from form parameter
                    company_id=current_user.company_id if hasattr(current_user, 'company_id') else None,
                    name=str(row.get('name', '')).strip(),
                    category=str(row.get('category', '')).strip() if row.get('category') else None,
                    sub_category=str(row.get('sub_category', '')).strip() if row.get('sub_category') else None,
                    description=str(row.get('description', '')).strip() if row.get('description') else None,
                    target_crops=str(row.get('target_crops', '')).strip() if row.get('target_crops') else None,
                    target_problems=str(row.get('target_problems', '')).strip() if row.get('target_problems') else None,
                    dosage=str(row.get('dosage', '')).strip() if row.get('dosage') else None,
                    usage_instructions=str(row.get('usage_instructions', '')).strip() if row.get('usage_instructions') else None,
                    safety_precautions=str(row.get('safety_precautions', '')).strip() if row.get('safety_precautions') else None,
                    price_range=str(row.get('price_range', '')).strip() if row.get('price_range') else None,
                    is_active=str(row.get('is_active', 'true')).lower() in ('true', '1', 'yes'),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                db.add(product)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
                error_count += 1
        
        print(f"✅ Upload Complete - Success: {success_count}, Errors: {error_count}")
        
        # Commit all products
        await db.commit()
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:10],  # Return first 10 errors
            "message": f"Successfully uploaded {success_count} products to brand '{brand.name}'" + 
                      (f" with {error_count} errors" if error_count > 0 else "")
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )
