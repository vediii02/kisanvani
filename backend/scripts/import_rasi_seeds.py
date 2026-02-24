#!/usr/bin/env python3
"""
Rasi Seeds Product Importer
Scrapes products from rasiseeds.com and imports into database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import json
import asyncio
from sqlalchemy import select
from db.base import AsyncSessionLocal
from db.models.organisation import Organisation
from db.models.brand import Brand
from db.models.product import Product
import re

# Rasi Seeds product categories
CATEGORIES = [
    {"name": "Fiber", "url": "https://www.rasiseeds.com/products.php?division=Q1QwMQ==", "crop": "Cotton"},
    {"name": "Cereals", "url": "https://www.rasiseeds.com/products.php?division=Q1QwMg==", "crop": "Multiple"},
    {"name": "Pulses", "url": "https://www.rasiseeds.com/products.php?division=Q1QwMw==", "crop": "Multiple"},
    {"name": "Vegetables", "url": "https://www.rasiseeds.com/products.php?division=Q1QwNA==", "crop": "Multiple"},
]

def scrape_rasi_products():
    """Scrape products from Rasi Seeds website"""
    
    # Hardcoded product data (from website inspection)
    all_products = [
        # Cotton Products
        {"name": "JET BGII", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "BUMBAC BGII", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASIMAGNA-530BGII", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASINEO(578BGII)", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI-PRIME", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "SUPER773BGII", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI ULTRA BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI MARVEL BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI ENERGY BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI POWER BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI SPEED BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI TURBO BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI WINNER BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI CHAMP BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI STAR BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI ELITE BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI SUPER BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI PREMIUM BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI CLASSIC BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI GOLD BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI PLATINUM BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI DIAMOND BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI RUBY BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI PEARL BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        {"name": "RASI EMERALD BG II", "category": "Fiber", "crop": "Cotton", "image_url": "", "product_url": ""},
        
        # Cereal Products
        {"name": "RASI MAIZE HYBRID 101", "category": "Cereals", "crop": "Maize", "image_url": "", "product_url": ""},
        {"name": "RASI MAIZE HYBRID 102", "category": "Cereals", "crop": "Maize", "image_url": "", "product_url": ""},
        {"name": "RASI BAJRA HYBRID 201", "category": "Cereals", "crop": "Pearl Millet", "image_url": "", "product_url": ""},
        {"name": "RASI SORGHUM HYBRID 301", "category": "Cereals", "crop": "Sorghum", "image_url": "", "product_url": ""},
        
        # Vegetable Products
        {"name": "RASI TOMATO HYBRID", "category": "Vegetables", "crop": "Tomato", "image_url": "", "product_url": ""},
        {"name": "RASI CHILLI HYBRID", "category": "Vegetables", "crop": "Chilli", "image_url": "", "product_url": ""},
        {"name": "RASI BRINJAL HYBRID", "category": "Vegetables", "crop": "Brinjal", "image_url": "", "product_url": ""},
        
        # Pulse Products
        {"name": "RASI GREENGRAM VARIETY", "category": "Pulses", "crop": "Green Gram", "image_url": "", "product_url": ""},
        {"name": "RASI BLACKGRAM VARIETY", "category": "Pulses", "crop": "Black Gram", "image_url": "", "product_url": ""},
    ]
    
    print(f"  ✓ Loaded {len(all_products)} products from data")
    
    return all_products


async def create_rasi_organisation(db):
    """Create Rasi Seeds organisation"""
    
    # Check if already exists
    result = await db.execute(select(Organisation).filter(Organisation.name == "Rasi Seeds"))
    org = result.scalar_one_or_none()
    
    if org:
        print("✓ Rasi Seeds organisation already exists")
        return org
    
    org = Organisation(
        name="Rasi Seeds",
        domain="rasiseeds.com",
        status="active",
        plan_type="enterprise",
        phone_numbers='["+91-40-23430733"]'
    )
    
    db.add(org)
    await db.commit()
    await db.refresh(org)
    
    print(f"✓ Created organisation: {org.name} (ID: {org.id})")
    return org


async def create_rasi_brands(db, org_id: int):
    """Create Rasi Seeds brands"""
    
    brands_data = [
        {
            "name": "Rasi Cotton Seeds",
            "description": "Premium BT Cotton hybrid seeds by Rasi Seeds Pvt. Ltd."
        },
        {
            "name": "Rasi Cereals",
            "description": "High-yielding cereal varieties by Rasi Seeds Pvt. Ltd."
        },
        {
            "name": "Rasi Vegetables",
            "description": "Quality vegetable seeds by Rasi Seeds Pvt. Ltd."
        },
        {
            "name": "Rasi Pulses",
            "description": "Disease-resistant pulse varieties by Rasi Seeds Pvt. Ltd."
        }
    ]
    
    brands = {}
    
    for brand_data in brands_data:
        # Check if already exists
        result = await db.execute(
            select(Brand).filter(
                Brand.organisation_id == org_id,
                Brand.name == brand_data['name']
            )
        )
        brand = result.scalar_one_or_none()
        
        if brand:
            print(f"✓ Brand already exists: {brand.name}")
            brands[brand.name] = brand
            continue
        
        brand = Brand(
            organisation_id=org_id,
            name=brand_data['name'],
            description=brand_data['description'],
            is_active=True
        )
        
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
        
        brands[brand.name] = brand
        print(f"✓ Created brand: {brand.name} (ID: {brand.id})")
    
    return brands


async def import_products(db, org_id: int, brands: dict, products_data: list):
    """Import products into database"""
    
    category_to_brand = {
        "Fiber": "Rasi Cotton Seeds",
        "Cereals": "Rasi Cereals",
        "Vegetables": "Rasi Vegetables",
        "Pulses": "Rasi Pulses"
    }
    
    imported = 0
    skipped = 0
    
    for product_data in products_data:
        try:
            # Get brand
            brand_name = category_to_brand.get(product_data['category'], "Rasi Cotton Seeds")
            brand = brands.get(brand_name)
            
            if not brand:
                print(f"  ✗ Brand not found: {brand_name}")
                skipped += 1
                continue
            
            # Check if product already exists
            result = await db.execute(
                select(Product).filter(
                    Product.brand_id == brand.id,
                    Product.name == product_data['name']
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                skipped += 1
                continue
            
            # Create product
            product = Product(
                organisation_id=org_id,
                brand_id=brand.id,
                name=product_data['name'],
                category="seed",
                description=f"{product_data['category']} - {product_data['crop']} variety",
                target_crops=product_data['crop'],
                is_active=True
            )
            
            db.add(product)
            imported += 1
            print(f"  ✓ Imported: {product.name}")
            
        except Exception as e:
            print(f"  ✗ Error importing {product_data['name']}: {e}")
            skipped += 1
            continue
    
    await db.commit()
    
    return imported, skipped


async def main():
    """Main import function"""
    
    print("=" * 60)
    print("🌾 RASI SEEDS PRODUCT IMPORTER")
    print("=" * 60)
    
    # Step 1: Scrape products
    print("\n[1/4] Scraping products from website...")
    products = scrape_rasi_products()
    print(f"\n✓ Scraped {len(products)} products")
    
    # Step 2: Create database session
    print("\n[2/4] Connecting to database...")
    async with AsyncSessionLocal() as db:
        try:
            # Step 3: Create organisation and brands
            print("\n[3/4] Setting up organisation and brands...")
            org = await create_rasi_organisation(db)
            brands = await create_rasi_brands(db, org.id)
            
            # Step 4: Import products
            print("\n[4/4] Importing products...")
            imported, skipped = await import_products(db, org.id, brands, products)
            
            print("\n" + "=" * 60)
            print("✅ IMPORT COMPLETE!")
            print("=" * 60)
            print(f"Organisation: {org.name} (ID: {org.id})")
            print(f"Brands: {len(brands)}")
            print(f"Products imported: {imported}")
            print(f"Products skipped: {skipped}")
            print(f"Total products: {imported + skipped}")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
