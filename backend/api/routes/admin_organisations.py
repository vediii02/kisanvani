# api/routes/admin_organisations.py
"""
Admin Organisations Management API
Allows admin role to manage all organisations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timezone

from core.auth import get_current_user, get_password_hash
from db.session import get_db
from db.models.organisation import Organisation
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
# GET: List All Organisations
# ============================================================================

@router.get("/organisations")
async def get_organisations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """
    Get list of all organisations (Admin only)
    Supports pagination and search
    """
    try:
        query = select(Organisation)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Organisation.name.ilike(search_term)) |
                (Organisation.domain.ilike(search_term))
            )
        
        # Apply status filter
        if status_filter:
            query = query.where(Organisation.status == status_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(Organisation)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                (Organisation.name.ilike(search_term)) |
                (Organisation.domain.ilike(search_term))
            )
        if status_filter:
            count_query = count_query.where(Organisation.status == status_filter)
        
        result = await db.execute(count_query)
        total = result.scalar()
        
        # Apply pagination
        query = query.order_by(Organisation.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        organisations = result.scalars().all()
        
        return {
            "success": True,
            "total": total,
            "skip": skip,
            "limit": limit,
            "organisations": [
                {
                    "id": org.id,
                    "name": org.name,
                    "domain": org.domain,
                    "status": org.status,
                    "plan_type": org.plan_type,
                    "phone_numbers": org.phone_numbers,
                    "primary_phone": org.primary_phone,
                    "preferred_languages": org.preferred_languages,
                    "greeting_message": org.greeting_message,
                    "created_at": org.created_at.isoformat() if org.created_at else None,
                    "updated_at": org.updated_at.isoformat() if org.updated_at else None,
                }
                for org in organisations
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching organisations: {str(e)}")


# ============================================================================
# GET: Single Organisation Details
# ============================================================================

@router.get("/organisations/{org_id}")
async def get_organisation(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Get details of a specific organisation"""
    query = select(Organisation).where(Organisation.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    return {
        "success": True,
        "organisation": {
            "id": org.id,
            "name": org.name,
            "domain": org.domain,
            "status": org.status,
            "plan_type": org.plan_type,
            "phone_numbers": org.phone_numbers,
            "primary_phone": org.primary_phone,
            "preferred_languages": org.preferred_languages,
            "greeting_message": org.greeting_message,
            "created_at": org.created_at.isoformat() if org.created_at else None,
            "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        }
    }


# ============================================================================
# POST: Create New Organisation
# ============================================================================

@router.post("/organisations")
async def create_organisation(
    organisation_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Create a new organisation (Admin only) and auto-create organisation user"""
    
    # Validate required fields
    if not organisation_data.get("name"):
        raise HTTPException(status_code=400, detail="Organisation name is required")
    
    if not organisation_data.get("domain"):
        raise HTTPException(status_code=400, detail="Organisation domain is required")
    
    if not organisation_data.get("username"):
        raise HTTPException(status_code=400, detail="Username is required for organisation login")
    
    if not organisation_data.get("password"):
        raise HTTPException(status_code=400, detail="Password is required for organisation login")
    
    if not organisation_data.get("email"):
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Check if domain already exists
    query = select(Organisation).where(Organisation.domain == organisation_data["domain"])
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"Organisation with domain '{organisation_data['domain']}' already exists")
    
    # Check if username already exists
    user_query = select(User).where(User.username == organisation_data["username"])
    user_result = await db.execute(user_query)
    existing_user = user_result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail=f"Username '{organisation_data['username']}' already exists")
    
    # Check if email already exists
    email_query = select(User).where(User.email == organisation_data["email"])
    email_result = await db.execute(email_query)
    existing_email = email_result.scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=400, detail=f"Email '{organisation_data['email']}' already exists")
    
    try:
        # Create new organisation
        new_org = Organisation(
            name=organisation_data["name"],
            domain=organisation_data["domain"],
            status=organisation_data.get("status", "active"),
            plan_type=organisation_data.get("plan_type", "basic"),
            phone_numbers=organisation_data.get("phone_numbers"),
            primary_phone=organisation_data.get("primary_phone"),
            preferred_languages=organisation_data.get("preferred_languages", "hi"),
            greeting_message=organisation_data.get("greeting_message"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(new_org)
        await db.commit()
        await db.refresh(new_org)
        
        # Create user for organisation
        org_user = User(
            username=organisation_data["username"],
            email=organisation_data["email"],
            hashed_password=get_password_hash(organisation_data["password"]),
            full_name=organisation_data["name"],
            role="organisation",
            organisation_id=new_org.id,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(org_user)
        await db.commit()
        await db.refresh(org_user)
        
        return {
            "success": True,
            "message": "Organisation and user created successfully",
            "organisation": {
                "id": new_org.id,
                "name": new_org.name,
                "domain": new_org.domain,
                "status": new_org.status,
                "username": org_user.username,
                "email": org_user.email
            }
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating organisation: {str(e)}")


# ============================================================================
# PUT: Update Organisation
# ============================================================================

@router.put("/organisations/{org_id}")
async def update_organisation(
    org_id: int,
    organisation_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Update an existing organisation (Admin only)"""
    
    query = select(Organisation).where(Organisation.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Check if domain is being changed and if new domain already exists
    if organisation_data.get("domain") and organisation_data["domain"] != org.domain:
        query = select(Organisation).where(
            Organisation.domain == organisation_data["domain"],
            Organisation.id != org_id
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail=f"Organisation with domain '{organisation_data['domain']}' already exists")
    
    try:
        # Update fields
        if "name" in organisation_data:
            org.name = organisation_data["name"]
        if "domain" in organisation_data:
            org.domain = organisation_data["domain"]
        if "status" in organisation_data:
            org.status = organisation_data["status"]
        if "plan_type" in organisation_data:
            org.plan_type = organisation_data["plan_type"]
        if "phone_numbers" in organisation_data:
            # Convert empty string to None for non-unique fields
            org.phone_numbers = organisation_data["phone_numbers"] or None
        if "primary_phone" in organisation_data:
            # Convert empty string to None to avoid unique constraint violation
            org.primary_phone = organisation_data["primary_phone"].strip() if organisation_data["primary_phone"] else None
        if "preferred_languages" in organisation_data:
            org.preferred_languages = organisation_data["preferred_languages"]
        if "greeting_message" in organisation_data:
            # Convert empty string to None
            org.greeting_message = organisation_data["greeting_message"] or None
        
        org.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(org)
        
        return {
            "success": True,
            "message": "Organisation updated successfully",
            "organisation": {
                "id": org.id,
                "name": org.name,
                "domain": org.domain,
                "status": org.status
            }
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating organisation: {str(e)}")


# ============================================================================
# DELETE: Delete Organisation
# ============================================================================

@router.delete("/organisations/{org_id}")
async def delete_organisation(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Delete an organisation (Admin only) - Hard delete with related records check"""
    
    query = select(Organisation).where(Organisation.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    try:
        # Check for related records
        from db.models.company import Company
        from db.models.brand import Brand
        from db.models.product import Product
        from db.models.user import User
        
        # Count related records
        companies_count = await db.execute(select(func.count()).select_from(Company).where(Company.organisation_id == org_id))
        brands_count = await db.execute(select(func.count()).select_from(Brand).where(Brand.organisation_id == org_id))
        products_count = await db.execute(select(func.count()).select_from(Product).where(Product.organisation_id == org_id))
        users_count = await db.execute(select(func.count()).select_from(User).where(User.organisation_id == org_id))
        
        companies = companies_count.scalar()
        brands = brands_count.scalar()
        products = products_count.scalar()
        users = users_count.scalar()
        
        # If there are related records, provide detailed error
        if any([companies, brands, products, users]):
            details = []
            if companies > 0:
                details.append(f"{companies} companies")
            if brands > 0:
                details.append(f"{brands} brands")
            if products > 0:
                details.append(f"{products} products")
            if users > 0:
                details.append(f"{users} users")
            
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete organisation. It has {', '.join(details)}. Please delete related records first or set status to inactive."
            )
        
        org_name = org.name
        # Hard delete if no related records
        await db.delete(org)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Organisation '{org_name}' deleted successfully"
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting organisation: {str(e)}")

    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching organisations: {str(e)}")


# ============================================================================
# GET: Single Organisation Details
# ============================================================================

@router.get("/organisations/{org_id}")
async def get_organisation(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Get details of a specific organisation"""
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    return {
        "success": True,
        "organisation": {
            "id": org.id,
            "name": org.name,
            "code": org.code,
            "business_type": org.business_type,
            "contact_person": org.contact_person,
            "contact_email": org.contact_email,
            "contact_phone": org.contact_phone,
            "address": org.address,
            "status": org.status,
            "created_at": org.created_at.isoformat() if org.created_at else None,
            "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        }
    }


# ============================================================================
# POST: Create New Organisation
# ============================================================================

@router.post("/organisations")
async def create_organisation(
    organisation_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Create a new organisation (Admin only)"""
    
    # Validate required fields
    if not organisation_data.get("name"):
        raise HTTPException(status_code=400, detail="Organisation name is required")
    
    if not organisation_data.get("code"):
        raise HTTPException(status_code=400, detail="Organisation code is required")
    
    # Check if code already exists
    existing = db.query(Organisation).filter(Organisation.code == organisation_data["code"]).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Organisation with code '{organisation_data['code']}' already exists")
    
    try:
        # Create new organisation
        new_org = Organisation(
            name=organisation_data["name"],
            code=organisation_data["code"],
            business_type=organisation_data.get("business_type"),
            contact_person=organisation_data.get("contact_person"),
            contact_email=organisation_data.get("contact_email"),
            contact_phone=organisation_data.get("contact_phone"),
            address=organisation_data.get("address"),
            status=organisation_data.get("status", "active"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(new_org)
        db.commit()
        db.refresh(new_org)
        
        return {
            "success": True,
            "message": "Organisation created successfully",
            "organisation": {
                "id": new_org.id,
                "name": new_org.name,
                "code": new_org.code,
                "status": new_org.status
            }
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating organisation: {str(e)}")


# ============================================================================
# PUT: Update Organisation
# ============================================================================

@router.put("/organisations/{org_id}")
async def update_organisation(
    org_id: int,
    organisation_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Update an existing organisation (Admin only)"""
    
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Check if code is being changed and if new code already exists
    if organisation_data.get("code") and organisation_data["code"] != org.code:
        existing = db.query(Organisation).filter(
            Organisation.code == organisation_data["code"],
            Organisation.id != org_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Organisation with code '{organisation_data['code']}' already exists")
    
    try:
        # Update fields
        if "name" in organisation_data:
            org.name = organisation_data["name"]
        if "code" in organisation_data:
            org.code = organisation_data["code"]
        if "business_type" in organisation_data:
            org.business_type = organisation_data["business_type"]
        if "contact_person" in organisation_data:
            org.contact_person = organisation_data["contact_person"]
        if "contact_email" in organisation_data:
            org.contact_email = organisation_data["contact_email"]
        if "contact_phone" in organisation_data:
            org.contact_phone = organisation_data["contact_phone"]
        if "address" in organisation_data:
            org.address = organisation_data["address"]
        if "status" in organisation_data:
            org.status = organisation_data["status"]
        
        org.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(org)
        
        return {
            "success": True,
            "message": "Organisation updated successfully",
            "organisation": {
                "id": org.id,
                "name": org.name,
                "code": org.code,
                "status": org.status
            }
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating organisation: {str(e)}")


# ============================================================================
# DELETE: Delete Organisation
# ============================================================================

@router.delete("/organisations/{org_id}")
async def delete_organisation(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_role)
):
    """Delete an organisation (Admin only)"""
    
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    try:
        # Soft delete by setting status to inactive
        org.status = "deleted"
        org.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return {
            "success": True,
            "message": f"Organisation '{org.name}' deleted successfully"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting organisation: {str(e)}")
