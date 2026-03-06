# api/routes/admin_organisations.py
"""
Admin Organisations Management API
Allows admin role to manage all organisations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from datetime import datetime, timezone
import json

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
                or_(
                    Organisation.name.ilike(search_term),
                    Organisation.email.ilike(search_term)
                )
            )
        
        # Apply status filter
        if status_filter:
            query = query.where(Organisation.status == status_filter)
        else:
            # Default filter: show only active and inactive
            query = query.where(Organisation.status.in_(['active', 'inactive']))
        
        # Get total count
        count_query = select(func.count()).select_from(Organisation)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                or_(
                    Organisation.name.ilike(search_term),
                    Organisation.email.ilike(search_term)
                )
            )
        if status_filter:
            count_query = count_query.where(Organisation.status == status_filter)
        else:
            count_query = count_query.where(Organisation.status.in_(['active', 'inactive']))
        
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
                    "email": org.email,
                    "status": org.status,
                    "plan_type": org.plan_type,
                    "phone_numbers": org.phone_numbers,
                    "secondary_phone": org.secondary_phone,
                    "address": org.address,
                    "city": org.city,
                    "state": org.state,
                    "pincode": org.pincode,
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
            "email": org.email,
            "status": org.status,
            "plan_type": org.plan_type,
            "phone_numbers": org.phone_numbers,
            "secondary_phone": org.secondary_phone,
            "address": org.address,
            "city": org.city,
            "state": org.state,
            "pincode": org.pincode,
            "website_link": org.website_link,
            "description": org.description,
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
    """Create a new organisation (Admin only)"""
    
    # Validate required fields
    if not organisation_data.get("name"):
        raise HTTPException(status_code=400, detail="Organisation name is required")
    
    try:
        # Create new organisation
        new_org = Organisation(
            name=organisation_data["name"],
            email=organisation_data.get("email"),
            status=organisation_data.get("status", "active"),
            plan_type=organisation_data.get("plan_type", "basic"),
            phone_numbers=organisation_data.get("phone_numbers"),
            secondary_phone=organisation_data.get("secondary_phone"),
            address=organisation_data.get("address"),
            city=organisation_data.get("city"),
            state=organisation_data.get("state"),
            pincode=organisation_data.get("pincode"),
            website_link=organisation_data.get("website_link"),
            description=organisation_data.get("description"),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(new_org)
        await db.commit()
        await db.refresh(new_org)
        
        return {
            "success": True,
            "message": "Organisation created successfully",
            "organisation": {
                "id": new_org.id,
                "name": new_org.name,
                "status": new_org.status
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
    
    try:
        # Update fields
        if "name" in organisation_data:
            org.name = organisation_data["name"]
        if "email" in organisation_data:
            org.email = organisation_data["email"]
        if "status" in organisation_data:
            org.status = organisation_data["status"]
        if "plan_type" in organisation_data:
            org.plan_type = organisation_data["plan_type"]
        if "phone_numbers" in organisation_data:
            org.phone_numbers = organisation_data["phone_numbers"]
        if "secondary_phone" in organisation_data:
            org.secondary_phone = organisation_data["secondary_phone"]

        if "address" in organisation_data:
            org.address = organisation_data["address"]
        if "city" in organisation_data:
            org.city = organisation_data["city"]
        if "state" in organisation_data:
            org.state = organisation_data["state"]
        if "pincode" in organisation_data:
            org.pincode = organisation_data["pincode"]
        if "website_link" in organisation_data:
            org.website_link = organisation_data["website_link"]
        if "description" in organisation_data:
            org.description = organisation_data["description"]
        
        org.updated_at = datetime.now(timezone.utc)
        
        # Sync with organisation admin user
        admin_user_result = await db.execute(
            select(User).where(User.organisation_id == org.id, User.role == 'organisation')
        )
        admin_user = admin_user_result.scalars().first()
        if admin_user:
            if "name" in organisation_data:
                admin_user.full_name = organisation_data["name"]
            if "email" in organisation_data and organisation_data["email"] != admin_user.email:
                admin_user.email = organisation_data["email"]
                admin_user.username = organisation_data["email"]
            if "status" in organisation_data:
                admin_user.status = organisation_data["status"]
            db.add(admin_user)

        await db.commit()
        await db.refresh(org)
        
        return {
            "success": True,
            "message": "Organisation updated successfully",
            "organisation": {
                "id": org.id,
                "name": org.name,
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
    """Delete an organisation (Admin only)"""
    
    query = select(Organisation).where(Organisation.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    try:
        org_name = org.name
        
        # Hard delete - database cascades will handle related records
        await db.delete(org)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Organisation '{org_name}' and all its related data deleted successfully"
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting organisation: {str(e)}")
