from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from core.auth import get_current_user
from db.session import get_db
from db.models.company import Company
from db.models.brand import Brand
from db.models.product import Product
from pydantic import BaseModel, Field
from typing import Optional, List
import pandas as pd
import io
from kb.loader import kb_loader

router = APIRouter()

class BrandCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None

class BrandResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    brand_id: Optional[int] = None
    category: str
    sub_category: Optional[str] = None
    description: Optional[str] = None
    target_crops: Optional[str] = None
    target_problems: Optional[str] = None
    dosage: Optional[str] = None
    usage_instructions: Optional[str] = None
    safety_precautions: Optional[str] = None
    price_range: Optional[str] = None
    is_active: bool = True

class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    sub_category: Optional[str] = None
    brand_id: Optional[int] = None
    brand_name: Optional[str] = None
    company_name: Optional[str] = None
    description: Optional[str] = None
    target_crops: Optional[str] = None
    target_problems: Optional[str] = None
    dosage: Optional[str] = None
    usage_instructions: Optional[str] = None
    safety_precautions: Optional[str] = None
    price_range: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None

@router.get("/brands", response_model=List[BrandResponse])
async def get_company_brands(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all brands for the current user's company"""
    if current_user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Access denied. Company role required.")
    
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="Company not found for user.")
    
    result = await db.execute(
        select(Brand).where(Brand.company_id == company_id).order_by(Brand.name)
    )
    brands = result.scalars().all()
    
    return [
        BrandResponse(
            id=brand.id,
            name=brand.name,
            description=brand.description,
            logo_url=brand.logo_url,
            is_active=brand.is_active,
            created_at=brand.created_at.isoformat() if brand.created_at else None
        )
        for brand in brands
    ]

@router.post("/brands", response_model=BrandResponse)
async def create_company_brand(
    brand_data: BrandCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new brand for the current user's company"""
    if current_user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Access denied. Company role required.")
    
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="Company not found for user.")
    
    # Get company details to get organisation_id
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")
    
    # Check if brand name already exists for this company
    existing_result = await db.execute(
        select(Brand).where(
            Brand.company_id == company_id,
            Brand.name == brand_data.name
        )
    )
    existing_brand = existing_result.scalar_one_or_none()
    
    if existing_brand:
        raise HTTPException(status_code=400, detail="Brand with this name already exists for your company.")
    
    # Create new brand
    new_brand = Brand(
        name=brand_data.name,
        organisation_id=company.organisation_id,
        company_id=company_id,
        description=brand_data.description,
        logo_url=brand_data.logo_url,
        is_active=True
    )
    
    db.add(new_brand)
    await db.commit()
    await db.refresh(new_brand)
    
    return BrandResponse(
        id=new_brand.id,
        name=new_brand.name,
        description=new_brand.description,
        logo_url=new_brand.logo_url,
        is_active=new_brand.is_active,
        created_at=new_brand.created_at.isoformat() if new_brand.created_at else None
    )

@router.put("/brands/{brand_id}", response_model=BrandResponse)
async def update_company_brand(
    brand_id: int,
    brand_data: BrandCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a brand for the current user's company"""
    if current_user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Access denied. Company role required.")
    
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="Company not found for user.")
    
    # Find the brand
    result = await db.execute(
        select(Brand).where(
            Brand.id == brand_id,
            Brand.company_id == company_id
        )
    )
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found.")
    
    # Check if brand name already exists for this company (excluding current brand)
    existing_result = await db.execute(
        select(Brand).where(
            Brand.company_id == company_id,
            Brand.name == brand_data.name,
            Brand.id != brand_id
        )
    )
    existing_brand = existing_result.scalar_one_or_none()
    
    if existing_brand:
        raise HTTPException(status_code=400, detail="Brand with this name already exists for your company.")
    
    # Update brand
    brand.name = brand_data.name
    brand.description = brand_data.description
    brand.logo_url = brand_data.logo_url
    if brand_data.is_active is not None:
        brand.is_active = brand_data.is_active
    
    await db.commit()
    await db.refresh(brand)
    
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        description=brand.description,
        logo_url=brand.logo_url,
        is_active=brand.is_active,
        created_at=brand.created_at.isoformat() if brand.created_at else None
    )

# ==================== Product Management ====================

@router.get("/products", response_model=List[ProductResponse])
async def get_company_products(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all products for the current user's company"""
    if current_user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Access denied. Company role required.")
    
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="Company not found for user.")
    
    result = await db.execute(
        select(Product).where(Product.company_id == company_id).order_by(Product.name)
    )
    products = result.scalars().all()
    
    # Fetch names for response
    response_data = []
    for product in products:
        brand_name = None
        company_name = None
        
        if product.brand_id:
            brand_res = await db.execute(select(Brand.name).where(Brand.id == product.brand_id))
            brand_name = brand_res.scalar()
            
        if product.company_id:
            co_res = await db.execute(select(Company.name).where(Company.id == product.company_id))
            company_name = co_res.scalar()
            
        response_data.append(
            ProductResponse(
                id=product.id,
                name=product.name,
                category=product.category,
                sub_category=product.sub_category,
                brand_id=product.brand_id,
                brand_name=brand_name,
                company_name=company_name,
                description=product.description,
                target_crops=product.target_crops,
                target_problems=product.target_problems,
                dosage=product.dosage,
                usage_instructions=product.usage_instructions,
                safety_precautions=product.safety_precautions,
                price_range=product.price_range,
                price=product.price,
                is_active=product.is_active,
                created_at=product.created_at.isoformat() if product.created_at else None
            )
        )
    
    return response_data

@router.post("/products", response_model=ProductResponse)
async def create_company_product(
    product_data: ProductCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new product for the current user's company"""
    if current_user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Access denied. Company role required.")
    
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="Company not found for user.")
    
    # Get company details to get organisation_id
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")
    
    # Check for duplicate product by name
    existing_product_result = await db.execute(
        select(Product).where(
            and_(
                func.lower(Product.name) == product_data.name.lower().strip(),
                Product.company_id == company_id
            )
        )
    )
    if existing_product_result.scalars().first():
        raise HTTPException(status_code=400, detail="A product with this name already exists for your company.")
    
    # Create new product
    new_product = Product(
        name=product_data.name,
        brand_id=product_data.brand_id,
        category=product_data.category,
        sub_category=product_data.sub_category,
        description=product_data.description,
        target_crops=product_data.target_crops,
        target_problems=product_data.target_problems,
        dosage=product_data.dosage,
        usage_instructions=product_data.usage_instructions,
        safety_precautions=product_data.safety_precautions,
        price_range=product_data.price_range,
        is_active=product_data.is_active,
        organisation_id=company.organisation_id,
        company_id=company_id
    )
    
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    # Automatically generate embedding in the background
    background_tasks.add_task(kb_loader.load_product_to_vector_db, new_product)
    
    # Get names for response
    brand_name = None
    if new_product.brand_id:
        brand_res = await db.execute(select(Brand.name).where(Brand.id == new_product.brand_id))
        brand_name = brand_res.scalar()
        
    return ProductResponse(
        id=new_product.id,
        name=new_product.name,
        category=new_product.category,
        sub_category=new_product.sub_category,
        brand_id=new_product.brand_id,
        brand_name=brand_name,
        company_name=company.name,
        description=new_product.description,
        target_crops=new_product.target_crops,
        target_problems=new_product.target_problems,
        dosage=new_product.dosage,
        usage_instructions=new_product.usage_instructions,
        safety_precautions=new_product.safety_precautions,
        price_range=new_product.price_range,
        is_active=new_product.is_active,
        created_at=new_product.created_at.isoformat() if new_product.created_at else None
    )

@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_company_product(
    product_id: int,
    product_data: ProductCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a product for the current user's company"""
    if current_user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Access denied. Company role required.")
    
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="Company not found for user.")
    
    # Find product
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.company_id == company_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    
    # Update only provided fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    
    # Automatically update embedding in the background
    background_tasks.add_task(kb_loader.load_product_to_vector_db, product)
    
    # Get names for response
    brand_name = None
    company_name = None
    
    if product.brand_id:
        brand_res = await db.execute(select(Brand.name).where(Brand.id == product.brand_id))
        brand_name = brand_res.scalar()
        
    if product.company_id:
        co_res = await db.execute(select(Company.name).where(Company.id == product.company_id))
        company_name = co_res.scalar()
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        category=product.category,
        sub_category=product.sub_category,
        brand_id=product.brand_id,
        brand_name=brand_name,
        company_name=company_name,
        description=product.description,
        target_crops=product.target_crops,
        target_problems=product.target_problems,
        dosage=product.dosage,
        usage_instructions=product.usage_instructions,
        safety_precautions=product.safety_precautions,
        price_range=product.price_range,
        is_active=product.is_active,
        created_at=product.created_at.isoformat() if product.created_at else None
    )

@router.delete("/products/{product_id}")
async def delete_company_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a product for the current user's company"""
    if current_user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Access denied. Company role required.")
    
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="Company not found for user.")
    
    # Find product
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.company_id == company_id
        )
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    
    await db.delete(product)
    await db.commit()
    
    return {"message": "Product deleted successfully"}

@router.post("/products/bulk-upload")
async def bulk_upload_products(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk upload products from CSV file for the current user's company"""
    if current_user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Access denied. Company role required.")
    
    # Get company_id from form or from user
    target_company_id = company_id if company_id else str(current_user.get("company_id"))
    if not target_company_id:
        raise HTTPException(status_code=404, detail="Company not found for user.")
    
    try:
        target_company_id = int(target_company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company_id format.")
    
    # Get company details to get organisation_id
    company_result = await db.execute(select(Company).where(Company.id == target_company_id))
    company = company_result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")
    
    # Get company brands for brand name mapping
    brands_result = await db.execute(select(Brand).where(Brand.company_id == target_company_id))
    brands = brands_result.scalars().all()
    brand_name_to_id = {brand.name: brand.id for brand in brands}
    
    # Read and process CSV file
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV, Excel files are supported.")
    
    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Validate required columns
    required_columns = ['name', 'category']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing_columns)}")
    
    # Process products
    imported_count = 0
    errors = []
    
    for index, row in df.iterrows():
        try:
            # Skip empty rows
            if pd.isna(row.get('name')) or pd.isna(row.get('category')):
                continue
            
            # Map brand name to brand_id if provided
            brand_id = None
            if 'brand_name' in row and pd.notna(row.get('brand_name')):
                brand_name = str(row['brand_name']).strip()
                if brand_name in brand_name_to_id:
                    brand_id = brand_name_to_id[brand_name]
                else:
                    # Create new brand if it doesn't exist
                    new_brand = Brand(
                        name=brand_name,
                        company_id=target_company_id,
                        organisation_id=company.organisation_id
                    )
                    db.add(new_brand)
                    await db.commit()
                    await db.refresh(new_brand)
                    brand_id = new_brand.id
                    brand_name_to_id[brand_name] = brand_id
            
            product_name = str(row['name']).strip()
            
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
                errors.append(f"Row {index + 1}: Product '{product_name}' already exists.")
                continue

            # Extract price safely
            price_val = None
            if 'price' in df.columns and pd.notna(row.get('price')):
                try:
                    price_str = str(row['price']).strip()
                    if price_str != '':
                        price_val = float(price_str)
                except (ValueError, TypeError):
                    pass

            # Create product
            product_data = {
                'name': product_name,
                'category': str(row['category']).strip(),
                'sub_category': str(row.get('sub_category', '')).strip() if pd.notna(row.get('sub_category')) else None,
                'description': str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
                'target_crops': str(row.get('target_crops', '')).strip() if pd.notna(row.get('target_crops')) else None,
                'target_problems': str(row.get('target_problems', '')).strip() if pd.notna(row.get('target_problems')) else None,
                'dosage': str(row.get('dosage', '')).strip() if pd.notna(row.get('dosage')) else None,
                'usage_instructions': str(row.get('usage_instructions', '')).strip() if pd.notna(row.get('usage_instructions')) else None,
                'safety_precautions': str(row.get('safety_precautions', '')).strip() if pd.notna(row.get('safety_precautions')) else None,
                'price_range': str(row.get('price_range', '')).strip() if pd.notna(row.get('price_range')) else None,
                'price': price_val,
                'is_active': True if pd.isna(row.get('is_active')) or str(row.get('is_active')).lower() == 'true' else False,
                'organisation_id': company.organisation_id,
                'company_id': target_company_id,
                'brand_id': brand_id
            }
            
            new_product = Product(**product_data)
            db.add(new_product)
            
            # Since we need the ID for the embedding system, we should flush the session
            # to get the ID without fully committing the entire transaction yet
            await db.flush()
            
            # Add to background tasks for vectorization
            background_tasks.add_task(kb_loader.load_product_to_vector_db, new_product)
            
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Row {index + 1}: {str(e)}")
    
    # Commit all products
    await db.commit()
    
    return {
        "results": {
            "imported": imported_count,
            "errors": len(errors),
            "error_details": errors[:10]  # Return first 10 errors
        },
        "message": f"Successfully imported {imported_count} products"
    }

@router.delete("/brands/{brand_id}")
async def delete_company_brand(
    brand_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a brand for the current user's company"""
    if current_user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Access denied. Company role required.")
    
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="Company not found for user.")
    
    # Find the brand
    result = await db.execute(
        select(Brand).where(
            Brand.id == brand_id,
            Brand.company_id == company_id
        )
    )
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found.")
    
    # Delete all associated products first
    from sqlalchemy import delete as sa_delete
    product_delete = await db.execute(
        sa_delete(Product).where(Product.brand_id == brand_id)
    )
    deleted_products = product_delete.rowcount
    
    await db.delete(brand)
    await db.commit()
    
    return {"message": f"Brand and {deleted_products} associated product(s) deleted successfully"}
