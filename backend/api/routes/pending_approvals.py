from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone

from core.auth import get_current_user
from db.session import get_db
from db.models.user import User
from db.models.organisation import Organisation
from db.models.company import Company

router = APIRouter()

# ============================================================================
# MIDDLEWARE: Verify Super Admin Role
# ============================================================================

async def verify_superadmin_role(current_user: dict = Depends(get_current_user)):
    """Verify that the current user has admin or superadmin role"""
    if current_user.get("role") not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Admin role required."
        )
    return current_user

# ============================================================================
# GET: Pending Organisation Approvals
# ============================================================================

@router.get("/pending-approvals")
async def get_pending_approvals(
    current_user: dict = Depends(verify_superadmin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get all pending organisation registration approvals"""
    
    # Find users with organisation role who are inactive (pending approval)
    # Join with organisations to get organisation details
    result = await db.execute(
        select(User, Organisation)
        .join(Organisation, User.organisation_id == Organisation.id)
        .where(
            and_(
                User.role == "organisation",
                User.status == "pending",
                Organisation.status == "pending"
            )
        )
        .order_by(User.created_at.desc())
    )
    
    pending_data = result.all()
    
    approvals = []
    for user, organisation in pending_data:
        approvals.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organisation_name": organisation.name,
            "organisation_id": organisation.id,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "status": "pending"
        })
    
    return {
        "pending_approvals": approvals,
        "total": len(approvals)
    }

# ============================================================================
# POST: Approve Organisation Registration
# ============================================================================

@router.post("/approve-user/{user_id}")
async def approve_user(
    user_id: int,
    current_user: dict = Depends(verify_superadmin_role),
    db: AsyncSession = Depends(get_db)
):
    """Approve a pending organisation user registration"""
    
    # Find the user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role != "organisation":
        raise HTTPException(status_code=400, detail="Only organisation users can be approved through this endpoint")
    
    if user.status == "active":
        raise HTTPException(status_code=400, detail="User is already approved")
    
    # Find the organisation
    org_result = await db.execute(select(Organisation).where(Organisation.id == user.organisation_id))
    organisation = org_result.scalar_one_or_none()
    
    # Approve the user and organisation
    user.status = "active"
    
    if organisation:
        organisation.status = "active"
        organisation.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return {
        "message": f"User {user.username} and organisation {organisation.name if organisation else 'Unknown'} approved successfully",
        "user_id": user.id,
        "username": user.username,
        "organisation_name": organisation.name if organisation else None
    }

# ============================================================================
# POST: Reject Organisation Registration
# ============================================================================

@router.post("/reject-user/{user_id}")
async def reject_user(
    user_id: int,
    current_user: dict = Depends(verify_superadmin_role),
    db: AsyncSession = Depends(get_db)
):
    """Reject a pending organisation user registration (soft-reject)"""
    
    # Find the user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role != "organisation":
        raise HTTPException(status_code=400, detail="Only organisation users can be rejected through this endpoint")
    
    # Find the organisation
    org_result = await db.execute(select(Organisation).where(Organisation.id == user.organisation_id))
    organisation = org_result.scalar_one_or_none()
    
    # Soft-reject: mark as rejected instead of deleting
    user.status = "rejected"
    
    if organisation:
        organisation.status = "rejected"
        organisation.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return {
        "message": f"User {user.username} and organisation {organisation.name if organisation else 'Unknown'} rejected successfully",
        "user_id": user_id,
        "username": user.username,
        "organisation_name": organisation.name if organisation else None
    }

# ============================================================================
# GET: Approval Statistics
# ============================================================================

@router.get("/approval-stats")
async def get_approval_stats(
    current_user: dict = Depends(verify_superadmin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get approval statistics for dashboard"""
    
    # Count pending approvals
    pending_result = await db.execute(
        select(User, Organisation)
        .join(Organisation, User.organisation_id == Organisation.id)
        .where(
            and_(
                User.role == "organisation",
                User.status == "pending",
                Organisation.status.in_(["active", "pending", "inactive"])
            )
        )
    )
    pending_data = pending_result.all()
    pending_count = len(pending_data)
    
    # Count approved organisations
    approved_result = await db.execute(
        select(Organisation).where(Organisation.status == "active")
    )
    approved_count = len(approved_result.scalars().all())
    
    # Count rejected organisations directly
    rejected_result = await db.execute(
        select(Organisation).where(Organisation.status == "rejected")
    )
    rejected_count = len(rejected_result.scalars().all())
    
    # Total organisations
    total_result = await db.execute(select(Organisation))
    total_count = len(total_result.scalars().all())
    
    # Today's registrations (only count users with valid organisation)
    today = datetime.now(timezone.utc).date()
    today_reg_result = await db.execute(
        select(User)
        .join(Organisation, User.organisation_id == Organisation.id)
        .where(
            and_(
                User.role == "organisation",
                Organisation.status.in_(["active", "pending", "inactive"]),
                User.created_at >= today
            )
        )
    )
    today_reg_count = len(today_reg_result.scalars().all())
    
    # Today's rejections
    today_rej_result = await db.execute(
        select(Organisation).where(
            and_(
                Organisation.status == "rejected",
                Organisation.updated_at >= today
            )
        )
    )
    today_rej_count = len(today_rej_result.scalars().all())
    
    return {
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "today_registrations": today_reg_count,
        "today_rejections": today_rej_count,
        "total_organisations": total_count
    }

# ============================================================================
# GET: Today's New Registrations
# ============================================================================

@router.get("/today-registrations")
async def get_today_registrations(
    current_user: dict = Depends(verify_superadmin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get today's new organisation registrations"""
    
    today = datetime.now(timezone.utc).date()
    
    result = await db.execute(
        select(User, Organisation)
        .join(Organisation, User.organisation_id == Organisation.id)
        .where(
            and_(
                User.role == "organisation",
                Organisation.status.in_(["active", "pending", "inactive"]),
                User.created_at >= today
            )
        )
        .order_by(User.created_at.desc())
    )
    
    registrations = []
    for user, organisation in result.all():
        registrations.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organisation_name": organisation.name,
            "organisation_id": organisation.id,
            "is_active": user.status == "active",
            "org_status": organisation.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    
    return {
        "today_registrations": registrations,
        "total": len(registrations)
    }

# ============================================================================
# GET: Today's Rejected Users
# ============================================================================

@router.get("/today-rejections")
async def get_today_rejections(
    current_user: dict = Depends(verify_superadmin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get today's rejected organisation registrations"""
    
    today = datetime.now(timezone.utc).date()
    
    result = await db.execute(
        select(User, Organisation)
        .join(Organisation, User.organisation_id == Organisation.id)
        .where(
            and_(
                User.role == "organisation",
                Organisation.status == "rejected",
                Organisation.updated_at >= today
            )
        )
        .order_by(Organisation.updated_at.desc())
    )
    
    rejections = []
    for user, organisation in result.all():
        rejections.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organisation_name": organisation.name,
            "organisation_id": organisation.id,
            "rejected_at": organisation.updated_at.isoformat() if organisation.updated_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    
    return {
        "today_rejections": rejections,
        "total": len(rejections)
    }

# ============================================================================
# GET: All Registrations (All Time)
# ============================================================================

@router.get("/all-registrations")
async def get_all_registrations(
    current_user: dict = Depends(verify_superadmin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get all organisation registrations for all time"""
    
    result = await db.execute(
        select(User, Organisation)
        .join(Organisation, User.organisation_id == Organisation.id)
        .where(
            and_(
                User.role == "organisation",
                Organisation.status.in_(["active", "pending", "inactive", "rejected"])
            )
        )
        .order_by(User.created_at.desc())
    )
    
    registrations = []
    for user, organisation in result.all():
        registrations.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organisation_name": organisation.name,
            "organisation_id": organisation.id,
            "is_active": user.status == "active",
            "org_status": organisation.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    
    return {
        "all_registrations": registrations,
        "total": len(registrations)
    }
