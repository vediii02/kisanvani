# backend/api/routes/products.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from db.session import get_db
from db.models.product import Product
from db.models.brand import Brand
from db.models.organisation import Organisation
from schemas.product import ProductResponse, ProductCreate, ProductUpdate
from core.auth import get_current_user
from db.models.user import User

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    organisation_id: Optional[int] = None,
    brand_id: Optional[int] = None,
    category: Optional[str] = None,
    target_crops: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all products with optional filters"""
    
    query = select(Product)
    
    # Apply filters
    if organisation_id:
        query = query.filter(Product.organisation_id == organisation_id)
    
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    
    if category:
        query = query.filter(Product.category == category)
    
    if target_crops:
        query = query.filter(Product.target_crops.contains(target_crops))
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get product by ID"""
    
    result = await db.execute(
        select(Product).filter(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.get("/brand/{brand_id}", response_model=List[ProductResponse])
async def get_products_by_brand(
    brand_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all products for a brand"""
    
    result = await db.execute(
        select(Product).filter(Product.brand_id == brand_id)
    )
    products = result.scalars().all()
    
    return products


@router.get("/organisation/{org_id}", response_model=List[ProductResponse])
async def get_products_by_organisation(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all products for an organisation"""
    
    result = await db.execute(
        select(Product).filter(Product.organisation_id == org_id)
    )
    products = result.scalars().all()
    
    return products


@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product"""
    
    # Verify brand exists
    result = await db.execute(
        select(Brand).filter(Brand.id == product.brand_id)
    )
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    new_product = Product(**product.dict())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    return new_product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a product"""
    
    result = await db.execute(
        select(Product).filter(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a product"""
    
    result = await db.execute(
        select(Product).filter(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.delete(product)
    await db.commit()
    
    return {"message": "Product deleted successfully"}
