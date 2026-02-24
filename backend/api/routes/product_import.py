"""
Product Import API - Bulk upload via CSV/Excel

Allows organisation admins to upload CSV or Excel files
to bulk import products into their organisation.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from db.models.product import Product
from db.models.brand import Brand
from db.models.organisation import Organisation
from core.dependencies import get_current_organisation_admin
import pandas as pd
import io
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()


class ProductImportService:
    """Service to handle bulk product import from CSV/Excel"""
    
    REQUIRED_COLUMNS = ['name', 'category']
    OPTIONAL_COLUMNS = [
        'brand_name', 'sub_category', 'description', 
        'composition', 'dosage', 'benefits', 'target_crops',
        'pack_size', 'mrp', 'is_active'
    ]
    
    @staticmethod
    def validate_file_type(filename: str) -> str:
        """Validate file extension"""
        if filename.endswith('.csv'):
            return 'csv'
        elif filename.endswith(('.xlsx', '.xls')):
            return 'excel'
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only CSV and Excel (.xlsx, .xls) files are supported."
            )
    
    @staticmethod
    async def parse_file(file_content: bytes, file_type: str) -> pd.DataFrame:
        """Parse CSV or Excel file into DataFrame"""
        try:
            if file_type == 'csv':
                df = pd.read_csv(io.BytesIO(file_content))
            else:  # excel
                df = pd.read_excel(io.BytesIO(file_content))
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
            
            return df
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse file: {str(e)}"
            )
    
    @staticmethod
    def validate_columns(df: pd.DataFrame) -> List[str]:
        """Validate required columns exist"""
        missing_columns = [col for col in ProductImportService.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Required: {', '.join(ProductImportService.REQUIRED_COLUMNS)}"
            )
        return list(df.columns)
    
    @staticmethod
    async def get_or_create_brand(
        db: AsyncSession,
        brand_name: str,
        organisation_id: int
    ) -> Brand:
        """Get existing brand or create new one"""
        # Try to find existing brand
        result = await db.execute(
            select(Brand).where(
                Brand.name == brand_name,
                Brand.organisation_id == organisation_id
            )
        )
        brand = result.scalar_one_or_none()
        
        if not brand:
            # Create new brand
            brand = Brand(
                name=brand_name,
                organisation_id=organisation_id,
                is_active=True
            )
            db.add(brand)
            await db.flush()  # Get the ID without committing
            logger.info(f"Created new brand: {brand_name} (ID: {brand.id})")
        
        return brand
    
    @staticmethod
    async def import_products(
        db: AsyncSession,
        df: pd.DataFrame,
        organisation_id: int,
        default_brand_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Import products from DataFrame"""
        results = {
            'total': len(df),
            'imported': 0,
            'failed': 0,
            'errors': [],
            'created_brands': set(),
            'skipped': 0
        }
        
        for index, row in df.iterrows():
            try:
                # Get brand name (from row or default)
                brand_name = str(row.get('brand_name', default_brand_name or 'Default Brand')).strip()
                
                if not brand_name:
                    results['errors'].append({
                        'row': index + 2,  # +2 for Excel row number (1-indexed + header)
                        'name': row.get('name', 'Unknown'),
                        'error': 'No brand name provided'
                    })
                    results['failed'] += 1
                    continue
                
                # Get or create brand
                brand = await ProductImportService.get_or_create_brand(
                    db, brand_name, organisation_id
                )
                results['created_brands'].add(brand_name)
                
                # Prepare product data
                product_name = str(row['name']).strip()
                category = str(row['category']).strip()
                
                # Check if product already exists
                existing_result = await db.execute(
                    select(Product).where(
                        Product.name == product_name,
                        Product.brand_id == brand.id
                    )
                )
                existing_product = existing_result.scalar_one_or_none()
                
                if existing_product:
                    results['skipped'] += 1
                    logger.info(f"Product '{product_name}' already exists, skipping")
                    continue
                
                # Create product
                product = Product(
                    name=product_name,
                    category=category,
                    brand_id=brand.id,
                    sub_category=str(row['sub_category']).strip() if pd.notna(row.get('sub_category')) else None,
                    description=str(row['description']).strip() if pd.notna(row.get('description')) else None,
                    composition=str(row['composition']).strip() if pd.notna(row.get('composition')) else None,
                    dosage=str(row['dosage']).strip() if pd.notna(row.get('dosage')) else None,
                    benefits=str(row['benefits']).strip() if pd.notna(row.get('benefits')) else None,
                    target_crops=str(row['target_crops']).strip() if pd.notna(row.get('target_crops')) else None,
                    pack_size=str(row['pack_size']).strip() if pd.notna(row.get('pack_size')) else None,
                    mrp=float(row['mrp']) if pd.notna(row.get('mrp')) else None,
                    is_active=bool(row.get('is_active', True))
                )
                
                db.add(product)
                results['imported'] += 1
                
            except Exception as e:
                logger.error(f"Error importing row {index + 2}: {e}")
                results['errors'].append({
                    'row': index + 2,
                    'name': row.get('name', 'Unknown'),
                    'error': str(e)
                })
                results['failed'] += 1
        
        # Commit all products
        try:
            await db.commit()
            logger.info(f"Successfully imported {results['imported']} products")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error committing products: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save products: {str(e)}"
            )
        
        results['created_brands'] = list(results['created_brands'])
        return results


@router.post("/upload")
async def upload_products_file(
    file: UploadFile = File(...),
    brand_name: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_organisation_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload CSV or Excel file to bulk import products
    
    **CSV/Excel Format:**
    Required columns:
    - name: Product name
    - category: Product category (e.g., Seeds, Pesticides, Fertilizers)
    
    Optional columns:
    - brand_name: Brand name (will be created if doesn't exist)
    - sub_category: Sub-category
    - description: Product description
    - composition: Chemical composition
    - dosage: Recommended dosage
    - benefits: Product benefits
    - target_crops: Crops this product is for
    - pack_size: Package size
    - mrp: Maximum Retail Price
    - is_active: true/false (default: true)
    
    **Example CSV:**
    ```
    name,category,brand_name,sub_category,description,mrp,is_active
    Super Seeds Pro,Seeds,MySeedBrand,Hybrid,High yield hybrid seeds,450,true
    Growth Fertilizer,Fertilizers,MyFertBrand,Organic,Organic NPK fertilizer,850,true
    ```
    """
    logger.info(f"Product import started by user: {current_user.get('username')} (Org: {current_user.get('organisation_id')})")
    
    # Validate file type
    file_type = ProductImportService.validate_file_type(file.filename)
    logger.info(f"Processing {file_type.upper()} file: {file.filename}")
    
    # Read file content
    file_content = await file.read()
    
    # Parse file
    df = await ProductImportService.parse_file(file_content, file_type)
    logger.info(f"Parsed {len(df)} rows from file")
    
    # Validate columns
    columns = ProductImportService.validate_columns(df)
    logger.info(f"Columns found: {', '.join(columns)}")
    
    # Import products
    results = await ProductImportService.import_products(
        db=db,
        df=df,
        organisation_id=current_user['organisation_id'],
        default_brand_name=brand_name
    )
    
    return {
        'success': True,
        'message': f'Import complete! {results["imported"]} products imported, {results["skipped"]} skipped, {results["failed"]} failed.',
        'results': results,
        'file_info': {
            'filename': file.filename,
            'type': file_type,
            'rows': len(df),
            'columns': columns
        }
    }


@router.get("/template/csv")
async def download_csv_template():
    """Download CSV template for product import"""
    from fastapi.responses import Response
    
    template = """name,category,brand_name,sub_category,description,composition,dosage,benefits,target_crops,pack_size,mrp,is_active
Super Seeds Pro,Seeds,MySeedBrand,Hybrid,High yield hybrid seeds,Hybrid F1,1 kg per acre,High germination rate,Rice|Wheat,1 kg,450,true
Growth Fertilizer,Fertilizers,MyFertBrand,Organic,Organic NPK fertilizer,NPK 19:19:19,2 kg per acre,Improves soil health,All crops,50 kg,850,true
Pest Control Spray,Pesticides,MyPestBrand,Insecticide,Effective against pests,Imidacloprid 17.8%,2 ml per liter,Quick action,Cotton|Vegetables,500 ml,320,true
"""
    
    return Response(
        content=template,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=products_import_template.csv"
        }
    )


@router.get("/template/excel")
async def download_excel_template():
    """Download Excel template for product import"""
    from fastapi.responses import Response
    
    # Create sample DataFrame
    data = {
        'name': ['Super Seeds Pro', 'Growth Fertilizer', 'Pest Control Spray'],
        'category': ['Seeds', 'Fertilizers', 'Pesticides'],
        'brand_name': ['MySeedBrand', 'MyFertBrand', 'MyPestBrand'],
        'sub_category': ['Hybrid', 'Organic', 'Insecticide'],
        'description': ['High yield hybrid seeds', 'Organic NPK fertilizer', 'Effective against pests'],
        'composition': ['Hybrid F1', 'NPK 19:19:19', 'Imidacloprid 17.8%'],
        'dosage': ['1 kg per acre', '2 kg per acre', '2 ml per liter'],
        'benefits': ['High germination rate', 'Improves soil health', 'Quick action'],
        'target_crops': ['Rice|Wheat', 'All crops', 'Cotton|Vegetables'],
        'pack_size': ['1 kg', '50 kg', '500 ml'],
        'mrp': [450, 850, 320],
        'is_active': [True, True, True]
    }
    
    df = pd.DataFrame(data)
    
    # Create Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Products')
    output.seek(0)
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=products_import_template.xlsx"
        }
    )
