# api/routes/admin_companies.py
"""
Admin Companies Management API
Allows admin role to manage all companies across all organisations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timezone

from core.auth import get_current_user, get_password_hash
from db.session import get_db
from db.models.company import Company
from db.models.organisation import Organisation
from db.models.brand import Brand
from db.models.product import Product
from db.models.user import User

router = APIRouter()

# ============================================================================
# MIDDLEWARE: Verify Admin Role
# ============================================================================

async def verify_admin_role(current_user: dict = Depends(get_current_user)):
    """Verify that the current user has admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access denied. Admin role required."
        )
    return current_user


# ============================================================================
# GET: List All Companies
# ============================================================================

@router.get("/companies")
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    organisation_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """
    Get list of all companies (Admin only)
    Supports pagination and search
    """
    try:
        query = select(Company).where(Company.status.in_(['active', 'inactive']))
        
        # Apply organisation filter
        if organisation_id:
            query = query.where(Company.organisation_id == organisation_id)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(Company.name.ilike(search_term))
        
        # Get total count
        count_query = select(func.count()).select_from(Company).where(Company.status.in_(['active', 'inactive']))
        if organisation_id:
            count_query = count_query.where(Company.organisation_id == organisation_id)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(Company.name.ilike(search_term))
        
        result = await db.execute(count_query)
        total = result.scalar()
        
        # Apply pagination
        query = query.order_by(Company.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        companies = result.scalars().all()
        
        # Get organisation names
        companies_data = []
        for company in companies:
            org_result = await db.execute(
                select(Organisation).where(Organisation.id == company.organisation_id)
            )
            org = org_result.scalar_one_or_none()
            
            # Get brand and product counts
            brand_count_result = await db.execute(
                select(func.count(Brand.id)).where(Brand.company_id == company.id)
            )
            brand_count = brand_count_result.scalar() or 0
            
            product_count_result = await db.execute(
                select(func.count(Product.id)).where(Product.company_id == company.id)
            )
            product_count = product_count_result.scalar() or 0
            
            companies_data.append({
                "id": company.id,
                "name": company.name,
                "organisation_id": company.organisation_id,
                "organisation_name": org.name if org else None,
                "email": company.email,
                "phone": company.phone,
                "secondary_phone": getattr(company, 'secondary_phone', None),
                "address": company.address,
                "city": company.city,
                "state": company.state,
                "pincode": company.pincode,
                "website_link": company.website_link,
                "description": company.description,
                "contact_person": company.contact_person,
                "brand_count": brand_count,
                "product_count": product_count,
                "status": company.status,
                "created_at": company.created_at.isoformat() if company.created_at else None,
            })
        
        return companies_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")


# ============================================================================
# GET: Single Company Details
# ============================================================================

@router.get("/companies/{company_id}")
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Get details of a specific company"""
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get organisation name
    org_result = await db.execute(
        select(Organisation).where(Organisation.id == company.organisation_id)
    )
    org = org_result.scalar_one_or_none()
    
    return {
        "id": company.id,
        "name": company.name,
        "organisation_id": company.organisation_id,
        "organisation_name": org.name if org else None,
        "email": company.email,
        "phone": company.phone,
        "secondary_phone": getattr(company, 'secondary_phone', None),
        "address": company.address,
        "city": company.city,
        "state": company.state,
        "pincode": company.pincode,
        "website_link": company.website_link,
        "description": company.description,
        "contact_person": company.contact_person,
        "status": company.status,
        "created_at": company.created_at.isoformat() if company.created_at else None,
    }


from schemas.company import CompanyCreateWithAdmin

@router.post("/companies")
async def create_company(
    company_input: CompanyCreateWithAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Create a new company (Admin only)"""
    
    # Verify organisation exists
    org_query = select(Organisation).where(Organisation.id == company_input.organisation_id)
    org_result = await db.execute(org_query)
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Check if username exists
    existing_user_result = await db.execute(select(User).where(User.username == company_input.username))
    existing_user = existing_user_result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    try:
        # Create company
        new_company = Company(
            name=company_input.name,
            organisation_id=company_input.organisation_id,
            email=str(company_input.email) if company_input.email else None,
            phone=company_input.phone,
            address=company_input.address,
            city=company_input.city,
            state=company_input.state,
            pincode=company_input.pincode,
            contact_person=company_input.contact_person,
            business_type=company_input.business_type,
            gst_number=company_input.gst_number,
            registration_number=company_input.registration_number,
            description=company_input.description,
            status=company_input.status,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(new_company)
        await db.flush() # Get company ID before creating user

        # Create company admin user (now mandatory)
        new_user = User(
            username=company_input.username,
            email=str(company_input.email) if company_input.email else f"{company_input.username}@system.com",
            hashed_password=get_password_hash(company_input.password),
            full_name=new_company.name,
            role="company",
            organisation_id=new_company.organisation_id,
            company_id=new_company.id,
            status="active"
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_company)
        
        return {
            "success": True,
            "message": "Company created successfully",
            "company": {
                "id": new_company.id,
                "name": new_company.name,
                "organisation_id": new_company.organisation_id
            },
            "admin_user": {
                "username": new_user.username,
                "password": company_input.password # Returning password for confirmation possibly? Keep consistent with old logic
            }
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating company: {str(e)}")


# ============================================================================
# PUT: Update Company
# ============================================================================

from schemas.company import CompanyUpdate

@router.put("/companies/{company_id}")
async def update_company(
    company_id: int,
    company_input: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Update an existing company (Admin only)"""
    
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        # Update fields using schema
        update_data = company_input.dict(exclude_unset=True)
        
        if "organisation_id" in update_data:
            # Verify new organisation exists
            org_query = select(Organisation).where(Organisation.id == update_data["organisation_id"])
            org_result = await db.execute(org_query)
            if not org_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Organisation not found")

        for field, value in update_data.items():
            if field == "email" and value:
                setattr(company, field, str(value))
            else:
                setattr(company, field, value)
        
        company.updated_at = datetime.now(timezone.utc)
        
        # Sync with company admin user
        admin_user_result = await db.execute(
            select(User).where(User.company_id == company.id, User.role == 'company')
        )
        admin_user = admin_user_result.scalars().first()
        if admin_user:
            if company_input.name:
                admin_user.full_name = company_input.name
            if company_input.email and str(company_input.email) != admin_user.email:
                admin_user.email = str(company_input.email)
            if company_input.status:
                admin_user.status = company_input.status
            db.add(admin_user)
            
        await db.commit()
        await db.refresh(company)
        
        return {
            "success": True,
            "message": "Company updated successfully",
            "company": {
                "id": company.id,
                "name": company.name,
                "organisation_id": company.organisation_id
            }
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating company: {str(e)}")


# ============================================================================
# DELETE: Delete Company
# ============================================================================

@router.delete("/companies/{company_id}")
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Delete a company (Admin only)"""
    
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        company_name = company.name
        # Check for related records
        from db.models.product import Product
        
        # Note: Brands don't have company_id yet (they only have organisation_id)
        # Only check products and users for now
        products_count = await db.execute(select(func.count()).select_from(Product).where(Product.company_id == company_id))
        users_count = await db.execute(select(func.count()).select_from(User).where(User.company_id == company_id))
        
        products = products_count.scalar()
        users = users_count.scalar()
        
        # Hard delete - database cascades will handle related records
        await db.delete(company)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Company '{company_name}' and all its related data deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")


# ============================================================================
# GET: List All Organisations (for dropdown)
# ============================================================================

@router.get("/organisations")
async def get_organisations(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Get list of all organisations for dropdown (Admin only)"""
    try:
        query = select(Organisation).where(Organisation.status == "active")
        result = await db.execute(query)
        organisations = result.scalars().all()
        
        return [
            {
                "id": org.id,
                "name": org.name,
                "domain": org.domain
            }
            for org in organisations
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching organisations: {str(e)}")
