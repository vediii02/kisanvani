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
# MIDDLEWARE: Verify Organisation Role
# ============================================================================

async def verify_organisation_role(current_user: dict = Depends(get_current_user)):
    """Verify that the current user has organisation role"""
    if current_user.get("role") != "organisation":
        raise HTTPException(
            status_code=403,
            detail="Access denied. Organisation role required."
        )
    return current_user

# ============================================================================
# GET: Pending Company User Approvals
# ============================================================================

@router.get("/pending-approvals")
async def get_pending_approvals(
    current_user: dict = Depends(verify_organisation_role),
    db: AsyncSession = Depends(get_db)
):
    """Get all pending company user registration approvals for this organisation"""
    
    # Get current user's organisation
    user_result = await db.execute(
        select(User).where(User.username == current_user["username"])
    )
    current_db_user = user_result.scalar_one_or_none()
    
    if not current_db_user or not current_db_user.organisation_id:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Find company users in this organisation who are inactive (pending approval)
    result = await db.execute(
        select(User)
        .options(selectinload(User.company))
        .where(
            and_(
                User.role == "company",
                User.status == "pending",
                User.organisation_id == current_db_user.organisation_id
            )
        )
        .order_by(User.created_at.desc())
    )
    
    pending_users = result.scalars().all()
    
    approvals = []
    for user in pending_users:
        if user.company and user.company.status in ["active", "pending"]:
            approvals.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "company_name": user.company.name,
                "company_id": user.company.id,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "status": "pending"
            })
    
    return {
        "pending_approvals": approvals,
        "total": len(approvals)
    }

# ============================================================================
# POST: Approve Company User Registration
# ============================================================================

@router.post("/approve-user/{user_id}")
async def approve_user(
    user_id: int,
    current_user: dict = Depends(verify_organisation_role),
    db: AsyncSession = Depends(get_db)
):
    """Approve a pending company user registration"""
    
    # Get current user's organisation
    user_result = await db.execute(
        select(User).where(User.username == current_user["username"])
    )
    current_db_user = user_result.scalar_one_or_none()
    
    if not current_db_user or not current_db_user.organisation_id:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Find the user to approve
    result = await db.execute(
        select(User)
        .options(selectinload(User.company))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role != "company":
        raise HTTPException(status_code=400, detail="Only company users can be approved through this endpoint")
    
    if user.status == "active":
        raise HTTPException(status_code=400, detail="User is already approved")
    
    # Verify the user belongs to the same organisation
    if user.organisation_id != current_db_user.organisation_id:
        raise HTTPException(status_code=403, detail="You can only approve users from your organisation")
    
    # Approve the user
    user.status = "active"
    
    if user.company:
        user.company.status = "active"
        user.company.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return {
        "message": f"User {user.username} approved successfully",
        "user_id": user.id,
        "username": user.username,
        "company_name": user.company.name if user.company else None
    }

# ============================================================================
# POST: Reject Company User Registration
# ============================================================================

@router.post("/reject-user/{user_id}")
async def reject_user(
    user_id: int,
    current_user: dict = Depends(verify_organisation_role),
    db: AsyncSession = Depends(get_db)
):
    """Reject a pending company user registration (soft-reject)"""
    
    # Get current user's organisation
    user_result = await db.execute(
        select(User).where(User.username == current_user["username"])
    )
    current_db_user = user_result.scalar_one_or_none()
    
    if not current_db_user or not current_db_user.organisation_id:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Find the user to reject
    result = await db.execute(
        select(User)
        .options(selectinload(User.company))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role != "company":
        raise HTTPException(status_code=400, detail="Only company users can be rejected through this endpoint")
    
    # Verify the user belongs to the same organisation
    if user.organisation_id != current_db_user.organisation_id:
        raise HTTPException(status_code=403, detail="You can only reject users from your organisation")
    
    # Soft-reject: mark as rejected instead of deleting
    user.status = "rejected"
    
    if user.company:
        user.company.status = "rejected"
        user.company.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return {
        "message": f"User {user.username} and company {user.company.name if user.company else 'Unknown'} rejected successfully",
        "user_id": user_id,
        "username": user.username,
        "company_name": user.company.name if user.company else None
    }

# ============================================================================
# GET: Approval Statistics
# ============================================================================

# ============================================================================
# GET: Approval Statistics
# ============================================================================

@router.get("/approval-stats")
async def get_approval_stats(
    current_user: dict = Depends(verify_organisation_role),
    db: AsyncSession = Depends(get_db)
):
    """Get approval statistics for organisation dashboard"""
    
    # Get current user's organisation
    user_result = await db.execute(
        select(User).where(User.username == current_user["username"])
    )
    current_db_user = user_result.scalar_one_or_none()
    
    if not current_db_user or not current_db_user.organisation_id:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Count pending approvals
    pending_result = await db.execute(
        select(User)
        .join(Company, User.company_id == Company.id)
        .where(
            and_(
                User.role == "company",
                User.status == "pending",
                User.organisation_id == current_db_user.organisation_id,
                Company.status.in_(["active", "pending", "inactive"])
            )
        )
    )
    pending_count = len(pending_result.scalars().all())
    
    # Count approved company users
    # Now specifically checking if the company was self-registered (via notes flag) to separate from admin-created users
    approved_result = await db.execute(
        select(User)
        .join(Company, User.company_id == Company.id)
        .where(
            and_(
                User.role == "company",
                User.status == "active",
                User.organisation_id == current_db_user.organisation_id
            )
        )
    )
    approved_count = len(approved_result.scalars().all())
    
    # Count rejected companies in this organisation
    rejected_result = await db.execute(
        select(Company).where(
            and_(
                Company.organisation_id == current_db_user.organisation_id,
                Company.status == "rejected"
            )
        )
    )
    rejected_count = len(rejected_result.scalars().all())
    
    # Today's registrations (only count users with valid company)
    today = datetime.now(timezone.utc).date()
    today_reg_result = await db.execute(
        select(User)
        .join(Company, User.company_id == Company.id)
        .where(
            and_(
                User.role == "company",
                User.organisation_id == current_db_user.organisation_id,
                User.status.in_(["active", "pending"]),
                Company.status.in_(["active", "pending", "inactive"]),
                User.created_at >= today
            )
        )
    )
    today_reg_count = len(today_reg_result.scalars().all())
    
    # Today's rejections
    today_rej_result = await db.execute(
        select(Company).where(
            and_(
                Company.organisation_id == current_db_user.organisation_id,
                Company.status == "rejected",
                Company.updated_at >= today
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
        "total_company_users": pending_count + approved_count + rejected_count
    }

# ============================================================================
# GET: Today's New Registrations (Organisation Level)
# ============================================================================

@router.get("/today-registrations")
async def get_today_registrations(
    current_user: dict = Depends(verify_organisation_role),
    db: AsyncSession = Depends(get_db)
):
    """Get today's new company user registrations for this organisation"""
    
    # Get current user's organisation
    user_result = await db.execute(
        select(User).where(User.username == current_user["username"])
    )
    current_db_user = user_result.scalar_one_or_none()
    
    if not current_db_user or not current_db_user.organisation_id:
        raise HTTPException(status_code=404, detail="Organisation not found")
        
    today = datetime.now(timezone.utc).date()
    
    result = await db.execute(
        select(User, Company)
        .join(Company, User.company_id == Company.id)
        .where(
            and_(
                User.role == "company",
                User.organisation_id == current_db_user.organisation_id,
                User.status.in_(["active", "pending"]),
                Company.status.in_(["active", "pending", "inactive"]),
                User.created_at >= today
            )
        )
        .order_by(User.created_at.desc())
    )
    
    registrations = []
    for user, company in result.all():
        registrations.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_name": company.name,
            "company_id": company.id,
            "is_active": user.status == "active",
            "company_status": company.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    
    return {
        "today_registrations": registrations,
        "total": len(registrations)
    }

# ============================================================================
# GET: Today's Rejected Users (Organisation Level)
# ============================================================================

@router.get("/today-rejections")
async def get_today_rejections(
    current_user: dict = Depends(verify_organisation_role),
    db: AsyncSession = Depends(get_db)
):
    """Get today's rejected company user registrations for this organisation"""
    
    # Get current user's organisation
    user_result = await db.execute(
        select(User).where(User.username == current_user["username"])
    )
    current_db_user = user_result.scalar_one_or_none()
    
    if not current_db_user or not current_db_user.organisation_id:
        raise HTTPException(status_code=404, detail="Organisation not found")
        
    today = datetime.now(timezone.utc).date()
    
    result = await db.execute(
        select(User, Company)
        .join(Company, User.company_id == Company.id)
        .where(
            and_(
                User.role == "company",
                User.organisation_id == current_db_user.organisation_id,
                Company.status == "rejected",
                Company.updated_at >= today
            )
        )
        .order_by(Company.updated_at.desc())
    )
    
    rejections = []
    for user, company in result.all():
        rejections.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_name": company.name,
            "company_id": company.id,
            "rejected_at": company.updated_at.isoformat() if company.updated_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    
    return {
        "today_rejections": rejections,
        "total": len(rejections)
    }

