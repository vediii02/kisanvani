"""
Super Admin API Routes - Platform Management
Only accessible to users with role='superadmin'
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from core.auth import get_current_super_admin
from db.session import get_db
from db.models.user import User
from db.models.organisation import Organisation
from db.models.company import Company
from sqlalchemy import delete as sa_delete
from db.models.brand import Brand
from db.models.product import Product
from db.models.audit import AuditLog, PlatformConfig, BannedProduct
from db.models.call_session import CallSession
from services.website_scraper import scraper

router = APIRouter()


# ===== Pydantic Schemas =====

class DashboardKPIs(BaseModel):
    total_organisations: int
    active_organisations: int
    total_companies: int
    total_brands: int
    total_products: int
    active_phone_numbers: int
    total_calls_today: int
    total_calls_month: int
    live_calls_count: int
    escalated_cases_count: int
    avg_ai_confidence: float
    total_users: int
    total_kb_entries: int


class DashboardStats(BaseModel):
    total_users: int
    total_admins: int
    total_company_users: int
    active_users: int
    inactive_users: int


class OrganisationStats(BaseModel):
    id: int
    name: str
    status: str
    is_active: bool
    brand_count: int
    product_count: int
    company_count: int = 0
    call_count: int
    phone_count: int
    phone_numbers: Optional[str]
    secondary_phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    plan_type: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    admin_username: Optional[str] = None
    created_at: str


class CallAnalytics(BaseModel):
    total_calls: int
    avg_duration_seconds: float
    ai_resolution_rate: float
    human_resolution_rate: float
    top_crops: List[dict]
    top_problems: List[dict]
    calls_by_hour: List[dict]


class AuditLogResponse(BaseModel):
    id: int
    username: str
    user_role: str
    action_type: str
    action_category: str
    description: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    organisation_id: Optional[int]
    severity: str
    created_at: str
    
    class Config:
        from_attributes = True


class PlatformConfigResponse(BaseModel):
    ai_confidence_threshold: int
    max_call_duration_minutes: int
    default_language: str
    stt_provider: str
    tts_provider: str
    llm_model: str
    embedding_model: Optional[str] = None
    rag_strictness_level: str
    rag_min_confidence: int
    force_kb_approval: bool
    enable_call_recording: bool
    enable_auto_escalation: bool
    trial_duration_days: int
    max_concurrent_calls: int
    updated_at: Optional[str]


class PlatformConfigUpdate(BaseModel):
    ai_confidence_threshold: Optional[int] = None
    max_call_duration_minutes: Optional[int] = None
    default_language: Optional[str] = None
    stt_provider: Optional[str] = None
    tts_provider: Optional[str] = None
    llm_model: Optional[str] = None
    rag_strictness_level: Optional[str] = None
    rag_min_confidence: Optional[int] = None
    force_kb_approval: Optional[bool] = None
    enable_call_recording: Optional[bool] = None
    enable_auto_escalation: Optional[bool] = None
    trial_duration_days: Optional[int] = None
    max_concurrent_calls: Optional[int] = None


# ===== Helper Functions =====

async def create_audit_log(
    db: AsyncSession,
    user: User,
    action_type: str,
    action_category: str,
    description: str,
    entity_type: str = None,
    entity_id: int = None,
    organisation_id: int = None,
    old_value: dict = None,
    new_value: dict = None,
    severity: str = "info",
    request: Request = None
):
    """Create an audit log entry"""
    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        user_role=user.role,
        action_type=action_type,
        action_category=action_category,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        organisation_id=organisation_id,
        old_value=old_value,
        new_value=new_value,
        severity=severity,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(audit)
    await db.commit()
    return audit


# ===== Dashboard KPIs =====

@router.get("/dashboard/kpis", response_model=DashboardKPIs)
async def get_dashboard_kpis(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    organisation_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get real-time platform-level KPIs"""
    
    # Date range
    today = datetime.now(timezone.utc).date()
    month_start = datetime(today.year, today.month, 1, tzinfo=timezone.utc)
    
    # Total organisations (excluding pending/rejected)
    org_result = await db.execute(select(func.count(Organisation.id)).where(Organisation.status.in_(['active', 'inactive'])))
    total_orgs = org_result.scalar() or 0
    
    # Active organisations
    active_org_result = await db.execute(
        select(func.count(Organisation.id)).where(Organisation.status == 'active')
    )
    active_orgs = active_org_result.scalar() or 0
    
    # Total companies (excluding pending/rejected)
    company_result = await db.execute(select(func.count(Company.id)).where(Company.status.in_(['active', 'inactive'])))
    total_companies = company_result.scalar() or 0
    
    # Total brands
    brand_result = await db.execute(select(func.count(Brand.id)))
    total_brands = brand_result.scalar() or 0
    
    # Total products
    product_result = await db.execute(select(func.count(Product.id)))
    total_products = product_result.scalar() or 0
    
    # Active phone numbers (from organisation_phone_numbers table)
    phone_result = await db.execute(
        text("SELECT COUNT(*) FROM organisation_phone_numbers")
    )
    active_phones = phone_result.scalar() or 0
    
    # Calls today
    calls_today_result = await db.execute(
        select(func.count(CallSession.id)).where(
            func.date(CallSession.created_at) == today
        )
    )
    calls_today = calls_today_result.scalar() or 0
    
    # Calls this month
    calls_month_result = await db.execute(
        select(func.count(CallSession.id)).where(
            CallSession.created_at >= month_start
        )
    )
    calls_month = calls_month_result.scalar() or 0
    
    # Live calls (status = 'ACTIVE')
    live_calls_result = await db.execute(
        text("SELECT COUNT(*) FROM call_sessions WHERE status = 'ACTIVE'")
    )
    live_calls = live_calls_result.scalar() or 0
    
    # Escalated cases
    escalated_result = await db.execute(
        text("SELECT COUNT(*) FROM escalations WHERE status != 'RESOLVED'")
    )
    escalated = escalated_result.scalar() or 0
    
    # Average AI confidence (placeholder - will be calculated from actual calls)
    avg_confidence = 75.0  # Default value
    
    # Total users
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0
    
    # Total KB entries
    kb_result = await db.execute(
        text("SELECT COUNT(*) FROM kb_entries")
    )
    total_kb = kb_result.scalar() or 0
    
    return {
        "total_organisations": total_orgs,
        "active_organisations": active_orgs,
        "total_companies": total_companies,
        "total_brands": total_brands,
        "total_products": total_products,
        "active_phone_numbers": active_phones,
        "total_calls_today": calls_today,
        "total_calls_month": calls_month,
        "live_calls_count": live_calls,
        "escalated_cases_count": escalated,
        "avg_ai_confidence": round(float(avg_confidence), 2),
        "total_users": total_users,
        "total_kb_entries": total_kb
    }


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get platform-level user statistics for Super Admin Dashboard"""
    
    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    
    # Total admins (organisation role, active/inactive only)
    total_admins_result = await db.execute(
        select(func.count(User.id)).where(and_(User.role == 'organisation', User.status.in_(['active', 'inactive'])))
    )
    total_admins = total_admins_result.scalar() or 0
    
    # Total company users (active/inactive only)
    total_company_users_result = await db.execute(
        select(func.count(User.id)).where(and_(User.role == 'company', User.status.in_(['active', 'inactive'])))
    )
    total_company_users = total_company_users_result.scalar() or 0
    
    # Active users
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == 'active')
    )
    active_users = active_users_result.scalar() or 0
    
    # Inactive users
    inactive_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == 'inactive')
    )
    inactive_users = inactive_users_result.scalar() or 0
    
    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_company_users": total_company_users,
        "active_users": active_users,
        "inactive_users": inactive_users
    }


# ===== Organisation Management =====

class OrganisationCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone_numbers: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    auto_import_products: bool = False
    username: str
    admin_password: str

class OrganisationUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_numbers: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/organisations")
async def create_organisation(
    org_data: OrganisationCreate,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Create a new organisation"""
    
    # Check if organisation name already exists
    existing_result = await db.execute(
        select(Organisation).where(Organisation.name == org_data.name)
    )
    existing_org = existing_result.scalar_one_or_none()
    
    if existing_org:
        raise HTTPException(
            status_code=400,
            detail=f"Organisation with name '{org_data.name}' already exists"
        )
    
    # Create organisation
    new_org = Organisation(
        name=org_data.name,
        email=org_data.email.strip() if org_data.email and org_data.email.strip() else None,
        phone_numbers=org_data.phone_numbers if org_data.phone_numbers else None,
        address=org_data.address,
        description=org_data.description,
        website_link=org_data.website_url,
        status='active'
    )
    
    db.add(new_org)
    await db.commit()
    await db.refresh(new_org)
    
    # Create default admin user for this organisation
    from core.auth import get_password_hash
    
    admin_user = None
    org_admin_username = org_data.username
    
    # Check if username already exists
    existing_user_result = await db.execute(
        select(User).where(User.username == org_admin_username)
    )
    existing_user = existing_user_result.scalar_one_or_none()
    
    if existing_user:
        # If organisation created but user exists, we might have a problem.
        # But since we just committed the org, we should proceed or rollback.
        # For simplicity, we'll raise an error.
        await db.delete(new_org) # Rollback org creation
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Username '{org_admin_username}' already exists"
        )

    admin_user = User(
        username=org_admin_username,
        email=(org_data.email.strip() if org_data.email and org_data.email.strip() else f"{org_admin_username}@{new_org.name.lower().replace(' ', '')}.com"),
        hashed_password=get_password_hash(org_data.admin_password),
        full_name=f"{new_org.name} Administrator",
        role="organisation",
        organisation_id=new_org.id,
        status="active"
    )
    db.add(admin_user)
    await db.commit()
    
    # Auto-import products if requested
    import_result = None
    if org_data.website_url and org_data.auto_import_products:
        try:
            scrape_result = await scraper.scrape_products(
                org_data.website_url,
                new_org.name
            )
            
            if scrape_result['success'] and scrape_result['products']:
                # Auto-create brand from website
                from urllib.parse import urlparse
                domain = urlparse(org_data.website_url).netloc
                brand_name = domain.replace('www.', '').split('.')[0].title()
                
                new_brand = Brand(
                    organisation_id=new_org.id,
                    name=brand_name,
                    description=f"Products from {org_data.website_url}",
                    is_active=True
                )
                db.add(new_brand)
                await db.commit()
                await db.refresh(new_brand)
                
                # Import products
                imported_count = 0
                for product_data in scrape_result['products'][:50]:  # Limit to 50 on creation
                    try:
                        new_product = Product(
                            organisation_id=new_org.id,
                            brand_id=new_brand.id,
                            name=product_data['name'],
                            category=product_data.get('category', 'other'),
                            sub_category=product_data.get('sub_category'),
                            description=product_data.get('description'),
                            price_range=product_data.get('price_range'),
                            price=product_data.get('price'),
                            is_active=True
                        )
                        db.add(new_product)
                        imported_count += 1
                    except Exception:
                        continue
                
                await db.commit()
                import_result = {
                    'imported': imported_count,
                    'total_found': scrape_result['total_found'],
                    'brand_id': new_brand.id,
                }
        except Exception as e:
            print(f"Auto-import failed: {e}")
            # Don't fail org creation if import fails
            pass
    
    # Get user for audit log
    user_result = await db.execute(
        select(User).where(User.username == current_user["username"])
    )
    user = user_result.scalar_one_or_none()
    
    # Create audit log
    await create_audit_log(
        db=db,
        user=user,
        action_type="organisation_create",
        action_category="organisation",
        description=f"Created organisation: {new_org.name}",
        entity_type="organisation",
        entity_id=new_org.id,
        new_value={"name": new_org.name, "status": new_org.status},
        severity="info",
        request=request
    )
    
    return {
        "success": True,
        "organisation": {
            "id": new_org.id,
            "name": new_org.name,
            "is_active": new_org.status == 'active'
        },
        "admin_user": {
            "username": admin_user.username,
            "password": org_data.admin_password,  # Send back only if just created
            "email": admin_user.email
        } if admin_user else None,
        "import_result": import_result
    }


@router.get("/organisations/{org_id}/products")
async def get_organisation_products(
    org_id: int,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all products for a specific organisation"""
    result = await db.execute(
        select(Product).where(Product.organisation_id == org_id)
    )
    products = result.scalars().all()

    product_list = []
    for p in products:
        # Get brand name
        brand_name = None
        if p.brand_id:
            brand_result = await db.execute(select(Brand.name).where(Brand.id == p.brand_id))
            brand_name = brand_result.scalar()

        product_list.append({
            "id": p.id,
            "name": p.name,
            "brand_id": p.brand_id,
            "brand_name": brand_name,
            "category": p.category,
            "sub_category": p.sub_category,
            "description": p.description,
            "target_crops": p.target_crops,
            "target_problems": p.target_problems,
            "dosage": p.dosage,
            "price": str(p.price) if p.price else None,
            "price_range": p.price_range,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })

    return product_list


@router.get("/organisations/stats", response_model=List[OrganisationStats])
async def get_organisations_stats(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all organisations with statistics"""
    
    query = select(Organisation).where(Organisation.status.in_(['active', 'inactive']))
    if status:
        if status == "active":
            query = select(Organisation).where(Organisation.status == 'active')
        elif status == "inactive":
            query = select(Organisation).where(Organisation.status == 'inactive')
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    orgs = result.scalars().all()
    
    stats_list = []
    for org in orgs:
        # Count brands
        brand_count = await db.execute(
            select(func.count(Brand.id)).where(Brand.organisation_id == org.id)
        )
        total_brands = brand_count.scalar() or 0
        
        # Count products
        product_count = await db.execute(
            select(func.count(Product.id)).where(Product.organisation_id == org.id)
        )
        total_products = product_count.scalar() or 0
        
        # Count companies
        company_count = await db.execute(
            select(func.count(Company.id)).where(Company.organisation_id == org.id)
        )
        total_companies = company_count.scalar() or 0
        
        # Count calls
        call_count = await db.execute(
            text(f"SELECT COUNT(*) FROM call_sessions WHERE organisation_id = {org.id}")
        )
        total_calls = call_count.scalar() or 0
        
        # Get admin user details
        admin_user_result = await db.execute(
            select(User).where(User.organisation_id == org.id, User.role == 'organisation')
        )
        admin_user = admin_user_result.scalars().first()
        
        # Get phone numbers
        phone_result = await db.execute(
            text(f"SELECT phone_number FROM organisation_phone_numbers WHERE organisation_id = {org.id}")
        )
        phones = [row[0] for row in phone_result.fetchall()]
        
        stats_list.append({
            "id": org.id,
            "name": org.name,
            "status": org.status,
            "is_active": org.status == 'active',
            "brand_count": total_brands,
            "product_count": total_products,
            "company_count": total_companies,
            "call_count": total_calls,
            "phone_count": len(phones),
            "phone_numbers": org.phone_numbers,
            "secondary_phone": org.secondary_phone,
            "email": org.email,
            "address": org.address,
            "city": org.city,
            "state": org.state,
            "pincode": org.pincode,
            "plan_type": org.plan_type,
            "description": org.description,
            "website_url": org.website_link,
            "admin_username": admin_user.username if admin_user else None,
            "created_at": org.created_at.isoformat() if org.created_at else ""
        })
    
    return stats_list


@router.patch("/organisations/{org_id}/status")
async def update_organisation_status(
    org_id: int,
    request: Request,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Activate or suspend an organisation"""
    body = await request.json()
    is_active = body.get("is_active", True)
    
    # Get organisation
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    old_status = org.status
    org.status = 'active' if is_active else 'inactive'
    
    # Cascade status to organisation admin
    admin_user_result = await db.execute(
        select(User).where(User.organisation_id == org.id, User.role == 'organisation')
    )
    admin_user = admin_user_result.scalars().first()
    if admin_user:
        admin_user.status = 'active' if is_active else 'inactive'
        db.add(admin_user)
    
    await db.commit()
    
    # Create audit log
    user_obj = await db.execute(select(User).where(User.username == current_user["username"]))
    user = user_obj.scalar_one()
    
    await create_audit_log(
        db=db,
        user=user,
        action_type="org_status_change",
        action_category="organisation",
        description=f"Changed organisation '{org.name}' status from {old_status} to {org.status}",
        entity_type="organisation",
        entity_id=org.id,
        organisation_id=org.id,
        old_value={"status": old_status},
        new_value={"status": org.status},
        severity="warning" if not is_active else "info",
        request=request
    )
    
    return {"success": True, "message": f"Organisation {'activated' if is_active else 'inactive'}"}


@router.put("/organisations/{org_id}")
async def update_organisation(
    org_id: int,
    request: Request,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update organisation details"""
    body = await request.json()
    print(f"[UPDATE ORG] org_id={org_id}, body={body}")

    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    old_name = org.name

    if "name" in body and body["name"]:
        org.name = body["name"].strip()
    if "email" in body:
        org.email = body["email"].strip() if body["email"] and body["email"].strip() else None
    if "phone_numbers" in body:
        org.phone_numbers = body["phone_numbers"].strip() if body["phone_numbers"] and body["phone_numbers"].strip() else None
    if "address" in body:
        org.address = body["address"]
    if "description" in body:
        org.description = body["description"]
    if "website_url" in body:
        org.website_link = body["website_url"]

    # Sync with Admin User
    admin_user_result = await db.execute(
        select(User).where(User.organisation_id == org.id, User.role == 'organisation')
    )
    admin_user = admin_user_result.scalars().first()
    print(f"[UPDATE ORG] admin_user found: {admin_user.username if admin_user else 'NONE'}")

    admin_username_saved = None

    if admin_user:
        # Determine the new username: explicit username field takes priority,
        # otherwise sync with the org name if it changed
        new_username = None
        if "username" in body and body["username"]:
            candidate = body["username"].strip()
            if candidate != admin_user.username:
                new_username = candidate
        elif "name" in body and body["name"] and body["name"].strip() != old_name:
            # Org name changed but no explicit username provided — sync username to new org name
            new_username = body["name"].strip().lower().replace(" ", "_")

        if new_username and new_username != admin_user.username:
            existing_user_result = await db.execute(
                select(User).where(User.username == new_username, User.id != admin_user.id)
            )
            if existing_user_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail=f"Username '{new_username}' already exists")
            admin_user.username = new_username
            print(f"[UPDATE ORG] Username updated to: {new_username}")
        
        # Update password if provided
        if "admin_password" in body and body["admin_password"]:
            from core.auth import get_password_hash
            admin_user.hashed_password = get_password_hash(body["admin_password"])
            
        # Update full name if organisation name changed
        admin_user.full_name = f"{org.name} Administrator"
        
        # Update email if provided
        if "email" in body:
            admin_user.email = body["email"].strip() if body["email"] and body["email"].strip() else None
        
        db.add(admin_user)
        admin_username_saved = admin_user.username
    else:
        print(f"[UPDATE ORG] WARNING: No admin user found for org_id={org.id}")
        
    db.add(org)
    await db.commit()
    await db.refresh(org)

    # Audit log
    user_result = await db.execute(select(User).where(User.username == current_user["username"]))
    user = user_result.scalar_one_or_none()
    if user:
        await create_audit_log(
            db=db,
            user=user,
            action_type="organisation_update",
            action_category="organisation",
            description=f"Updated organisation: {org.name}",
            entity_type="organisation",
            entity_id=org.id,
            organisation_id=org.id,
            new_value={"name": org.name},
            severity="info",
            request=request,
        )

    return {
        "success": True,
        "organisation": {
            "id": org.id,
            "name": org.name,
            "admin_username": admin_username_saved,
        },
    }


@router.delete("/organisations/{org_id}")
async def delete_organisation(
    org_id: int,
    request: Request,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete an organisation"""
    result = await db.execute(select(Organisation).where(Organisation.id == org_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    org_name = org.name

    # Audit log before deletion
    user_result = await db.execute(select(User).where(User.username == current_user["username"]))
    user = user_result.scalar_one_or_none()
    if user:
        await create_audit_log(
            db=db,
            user=user,
            action_type="organisation_delete",
            action_category="organisation",
            description=f"Deleted organisation: {org_name}",
            entity_type="organisation",
            entity_id=org.id,
            organisation_id=org.id,
            old_value={"name": org_name},
            severity="warning",
            request=request,
        )

    # Hard delete - database cascades will handle related records (users, companies, brands, products)
    await db.delete(org)
    await db.commit()

    return {"success": True, "message": f"Organisation '{org_name}' deleted successfully"}


# ===== Platform Configuration =====

@router.get("/platform/config", response_model=PlatformConfigResponse)
async def get_platform_config(
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get platform configuration"""
    result = await db.execute(select(PlatformConfig).limit(1))
    config = result.scalar_one_or_none()
    
    if not config:
        # Create default config
        config = PlatformConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)
    
    return PlatformConfigResponse(
        ai_confidence_threshold=config.ai_confidence_threshold,
        max_call_duration_minutes=config.max_call_duration_minutes,
        default_language=config.default_language,
        stt_provider=config.stt_provider,
        tts_provider=config.tts_provider,
        llm_model=config.llm_model,
        embedding_model="google" if config.llm_model == "gemini" else "openai",
        rag_strictness_level=config.rag_strictness_level,
        rag_min_confidence=config.rag_min_confidence,
        force_kb_approval=config.force_kb_approval,
        enable_call_recording=config.enable_call_recording,
        enable_auto_escalation=config.enable_auto_escalation,
        trial_duration_days=config.trial_duration_days,
        max_concurrent_calls=config.max_concurrent_calls,
        updated_at=config.updated_at.isoformat() if config.updated_at else None
    )


@router.put("/platform/config")
async def update_platform_config(
    config_update: PlatformConfigUpdate,
    request: Request,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    # Get current config
    result = await db.execute(select(PlatformConfig).limit(1))
    config = result.scalar_one_or_none()
    
    if not config:
        config = PlatformConfig()
        db.add(config)
    
    # Store old values
    old_values = {}
    new_values = {}
    
    # Update fields
    update_data = config_update.dict(exclude_unset=True)
    
    # Server-side Normalization: Force supported values only
    SUPPORTED_STT = ["sarvam", "google"]
    SUPPORTED_TTS = ["sarvam", "google"]
    SUPPORTED_LLM = ["groq", "openai", "gemini"]
    
    if "stt_provider" in update_data and update_data["stt_provider"] not in SUPPORTED_STT:
        update_data["stt_provider"] = "sarvam"
    if "tts_provider" in update_data and update_data["tts_provider"] not in SUPPORTED_TTS:
        update_data["tts_provider"] = "sarvam"
    if "llm_model" in update_data and update_data["llm_model"] not in SUPPORTED_LLM:
        # Fallback to current or default
        update_data["llm_model"] = update_data.get("llm_model", config.llm_model if config.llm_model in SUPPORTED_LLM else "groq")
        if update_data["llm_model"] not in SUPPORTED_LLM:
            update_data["llm_model"] = "groq"

    for field, value in update_data.items():
        old_values[field] = getattr(config, field)
        setattr(config, field, value)
        new_values[field] = value
    
    # Get user
    user_result = await db.execute(select(User).where(User.username == current_user["username"]))
    user = user_result.scalar_one()
    
    config.updated_by = user.id
    config.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    # Invalidate config cache so services pick up changes immediately
    try:
        from services.config_service import invalidate_config_cache
        invalidate_config_cache()
    except Exception:
        pass  # Don't fail the request if cache invalidation fails
    
    # Print active providers for easy verification via docker logs
    print(f"\n{'='*60}")
    print(f"✅ AI CONFIG UPDATED SUCCESSFULLY")
    print(f"   LLM Provider : {config.llm_model}")
    print(f"   STT Provider : {config.stt_provider}")
    print(f"   TTS Provider : {config.tts_provider}")
    print(f"   Language     : {config.default_language}")
    print(f"{'='*60}\n")
    
    # Create audit log
    await create_audit_log(
        db=db,
        user=user,
        action_type="platform_config_change",
        action_category="config",
        description=f"Updated platform configuration: {', '.join(update_data.keys())}",
        entity_type="platform_config",
        entity_id=config.id,
        old_value=old_values,
        new_value=new_values,
        severity="critical",
        request=request
    )
    
    return {"success": True, "message": "Platform configuration updated"}


# ===== Audit Logs =====

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    action_category: Optional[str] = Query(None),
    organisation_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs with filters"""
    
    query = select(AuditLog)
    
    # Apply filters
    if action_category:
        query = query.where(AuditLog.action_category == action_category)
    if organisation_id:
        query = query.where(AuditLog.organisation_id == organisation_id)
    if severity:
        query = query.where(AuditLog.severity == severity)
    if start_date:
        query = query.where(AuditLog.timestamp >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(AuditLog.timestamp <= datetime.fromisoformat(end_date))
    
    # Order by most recent
    query = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        AuditLogResponse(
            id=log.id,
            username=log.username,
            user_role=log.user_role,
            action_type=log.action_type,
            action_category=log.action_category,
            description=log.description,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            organisation_id=log.organisation_id,
            severity=log.severity,
            created_at=log.timestamp.isoformat()
        )
        for log in logs
    ]


# ===== Banned Products Management =====

@router.get("/banned-products")
async def get_banned_products(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all globally banned products"""
    result = await db.execute(
        select(BannedProduct)
        .where(BannedProduct.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/banned-products")
async def ban_product(
    product_name: str,
    ban_reason: str,
    chemical_name: Optional[str] = None,
    regulatory_reference: Optional[str] = None,
    request: Request = None,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Globally ban a product"""
    
    # Get user
    user_result = await db.execute(select(User).where(User.username == current_user["username"]))
    user = user_result.scalar_one()
    
    banned_product = BannedProduct(
        product_name=product_name,
        chemical_name=chemical_name,
        ban_reason=ban_reason,
        regulatory_reference=regulatory_reference,
        banned_by_user=user.id
    )
    
    db.add(banned_product)
    await db.commit()
    
    # Audit log
    await create_audit_log(
        db=db,
        user=user,
        action_type="product_ban",
        action_category="product",
        description=f"Globally banned product: {product_name}",
        entity_type="banned_product",
        entity_id=banned_product.id,
        new_value={"product_name": product_name, "ban_reason": ban_reason},
        severity="critical",
        request=request
    )
    
    return {"success": True, "message": f"Product '{product_name}' banned globally"}


# ===== Organisation Phone Numbers =====

@router.get("/organisations/{organisation_id}/phone-numbers")
async def get_organisation_phone_numbers(
    organisation_id: int,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all phone numbers for a specific organisation"""
    
    # Verify organisation exists
    org_result = await db.execute(
        select(Organisation).where(Organisation.id == organisation_id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Get phone numbers
    phone_result = await db.execute(
        text("""
            SELECT id, phone_number, channel, status, region, created_at
            FROM organisation_phone_numbers
            WHERE organisation_id = :org_id
            ORDER BY created_at DESC
        """),
        {"org_id": organisation_id}
    )
    
    phones = []
    for row in phone_result:
        phones.append({
            "id": row[0],
            "phone_number": row[1],
            "channel": row[2],
            "status": row[3],
            "region": row[4],
            "created_at": row[5].isoformat() if row[5] else None
        })
    
    return phones


# ===== Import Products from Website =====

class WebsiteImportRequest(BaseModel):
    website_url: str
    brand_id: Optional[int] = None
    auto_create_brand: bool = True


@router.post("/organisations/{organisation_id}/import-from-website")
async def import_products_from_website(
    organisation_id: int,
    request_data: WebsiteImportRequest,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    Import products from a company website
    Scrapes the website and automatically creates products
    """
    
    # Verify organisation exists
    org_result = await db.execute(
        select(Organisation).where(Organisation.id == organisation_id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    
    # Get user from DB
    user_result = await db.execute(
        select(User).where(User.id == current_user["user_id"])
    )
    user = user_result.scalar_one_or_none()
    
    # Scrape website
    scrape_result = await scraper.scrape_products(
        request_data.website_url,
        org.name
    )
    
    if not scrape_result['success']:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to scrape website: {scrape_result['error']}"
        )
    
    if not scrape_result['products']:
        raise HTTPException(
            status_code=400,
            detail="No products found on the website. Please check the URL or try a different page."
        )
    
    # Determine brand to use
    brand_id = request_data.brand_id
    
    if not brand_id and request_data.auto_create_brand:
        # Auto-create brand from website domain
        from urllib.parse import urlparse
        domain = urlparse(request_data.website_url).netloc
        brand_name = domain.replace('www.', '').split('.')[0].title()
        
        # Check if brand already exists
        brand_result = await db.execute(
            select(Brand).where(
                and_(
                    Brand.organisation_id == organisation_id,
                    Brand.name == brand_name
                )
            )
        )
        existing_brand = brand_result.scalar_one_or_none()
        
        if existing_brand:
            brand_id = existing_brand.id
        else:
            # Create new brand
            new_brand = Brand(
                organisation_id=organisation_id,
                name=brand_name,
                description=f"Products from {request_data.website_url}",
                is_active=True
            )
            db.add(new_brand)
            await db.commit()
            await db.refresh(new_brand)
            brand_id = new_brand.id
    
    if not brand_id:
        raise HTTPException(
            status_code=400,
            detail="Brand ID required. Set brand_id or enable auto_create_brand."
        )
    
    # Import products
    imported_count = 0
    skipped_count = 0
    
    for product_data in scrape_result['products']:
        try:
            # Check if product already exists (by name)
            existing_result = await db.execute(
                select(Product).where(
                    and_(
                        Product.organisation_id == organisation_id,
                        Product.name == product_data['name']
                    )
                )
            )
            existing_product = existing_result.scalar_one_or_none()
            
            if existing_product:
                skipped_count += 1
                continue
            
            # Create new product
            new_product = Product(
                organisation_id=organisation_id,
                brand_id=brand_id,
                name=product_data['name'],
                category=product_data.get('category', 'other'),
                sub_category=product_data.get('sub_category'),
                description=product_data.get('description'),
                target_crops=product_data.get('target_crops'),
                target_problems=product_data.get('target_problems'),
                dosage=product_data.get('dosage'),
                usage_instructions=product_data.get('usage_instructions'),
                safety_precautions=product_data.get('safety_precautions'),
                price_range=product_data.get('price_range'),
                price=product_data.get('price'),
                is_active=True
            )
            
            db.add(new_product)
            imported_count += 1
            
        except Exception as e:
            print(f"Error importing product {product_data.get('name')}: {e}")
            continue
    
    await db.commit()
    
    # Create audit log
    await create_audit_log(
        db=db,
        user=user,
        action_type="product_import",
        action_category="product",
        description=f"Imported {imported_count} products from {request_data.website_url}",
        entity_type="product",
        entity_id=brand_id,
        new_value={
            "website_url": request_data.website_url,
            "imported": imported_count,
            "skipped": skipped_count,
            "total_found": scrape_result['total_found']
        },
        severity="info",
        request=request
    )
    
    return {
        "success": True,
        "message": f"Successfully imported {imported_count} products",
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "total_found": scrape_result['total_found'],
        "brand_id": brand_id
    }


# ===== Call Analytics =====

@router.get("/call-analytics")
async def get_call_analytics(
    time_range: str = Query("today", alias="range"),  # today, week, month, all
    organisation_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed call analytics"""
    from datetime import date
    
    # Determine date range
    today = date.today()
    if time_range == "today":
        start_date = today
    elif time_range == "week":
        start_date = today - timedelta(days=7)
    elif time_range == "month":
        start_date = today - timedelta(days=30)
    else:
        start_date = None
    
    # Base query
    query = select(CallSession)
    if start_date:
        query = query.where(func.date(CallSession.created_at) >= start_date)
    if organisation_id:
        query = query.where(CallSession.organisation_id == organisation_id)
    
    result = await db.execute(query)
    calls = result.scalars().all()
    
    if not calls:
        return {
            "total_calls": 0,
            "avg_duration_seconds": 0,
            "ai_resolution_rate": 0,
            "human_resolution_rate": 0,
            "top_crops": [],
            "top_problems": [],
            "calls_by_hour": [],
            "org_distribution": []
        }
    
    # Calculate metrics
    total_calls = len(calls)
    total_duration = sum([c.duration_seconds or 0 for c in calls])
    avg_duration = total_duration / total_calls if total_calls > 0 else 0
    
    # Resolution rates (placeholder - would need actual data)
    ai_resolved = sum([1 for c in calls if c.status == 'completed'])
    ai_resolution_rate = (ai_resolved / total_calls * 100) if total_calls > 0 else 0
    human_resolution_rate = 100 - ai_resolution_rate
    
    # Top crops (from farmer_info JSON field or mocked for UI)
    crop_counts = {}
    for call in calls:
        # Check if farmer_info exists on the model
        if hasattr(call, 'farmer_info') and call.farmer_info and isinstance(call.farmer_info, dict):
            crop = call.farmer_info.get('crop')
            if crop:
                crop_counts[crop] = crop_counts.get(crop, 0) + 1
                
    if not crop_counts:
        # Provide placeholder data if no crops were extracted from actual data
        top_crops = [
            {"crop": "Wheat", "count": int(total_calls * 0.4)},
            {"crop": "Rice", "count": int(total_calls * 0.3)},
            {"crop": "Cotton", "count": int(total_calls * 0.2)},
            {"crop": "Sugarcane", "count": int(total_calls * 0.1)}
        ]
    else:
        top_crops = [{"crop": crop, "count": count} for crop, count in sorted(crop_counts.items(), key=lambda x: x[1], reverse=True)]
    
    # Top problems (placeholder)
    top_problems = [
        {"problem": "Yellowing leaves", "count": int(total_calls * 0.3)},
        {"problem": "Pest attack", "count": int(total_calls * 0.25)},
        {"problem": "Wilting", "count": int(total_calls * 0.2)},
        {"problem": "Disease", "count": int(total_calls * 0.15)},
        {"problem": "Other", "count": int(total_calls * 0.1)}
    ]
    
    # Calls by hour
    hour_counts = {}
    for call in calls:
        if call.created_at:
            hour = call.created_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    calls_by_hour = [{"hour": h, "count": hour_counts.get(h, 0)} for h in range(24)]
    
    # Organisation distribution
    org_counts = {}
    for call in calls:
        if call.organisation_id:
            org_counts[call.organisation_id] = org_counts.get(call.organisation_id, 0) + 1
    
    # Get organisation names
    org_distribution = []
    for org_id, count in org_counts.items():
        org_result = await db.execute(select(Organisation).where(Organisation.id == org_id))
        org = org_result.scalar_one_or_none()
        if org:
            org_distribution.append({
                "organisation_name": org.name,
                "call_count": count
            })
    
    return {
        "total_calls": total_calls,
        "avg_duration_seconds": round(avg_duration, 2),
        "ai_resolution_rate": round(ai_resolution_rate, 2),
        "human_resolution_rate": round(human_resolution_rate, 2),
        "top_crops": top_crops[:10],
        "top_problems": top_problems,
        "calls_by_hour": calls_by_hour,
        "org_distribution": sorted(org_distribution, key=lambda x: x['call_count'], reverse=True)
    }
    

@router.get("/calls")
async def get_superadmin_calls(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    organisation_id: Optional[int] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_super_admin)
):
    """
    Get all call logs across the platform for Superadmin.
    Supports filtering by organisation and company.
    """
    from db.models.call_summary import CallSummary
    from db.models.farmer import Farmer
    from db.models.call_metrics import CallMetrics
    
    query = select(CallSession, CallSummary, Farmer, CallMetrics).outerjoin(
        CallSummary, CallSession.id == CallSummary.call_session_id
    ).outerjoin(
        Farmer, CallSession.farmer_id == Farmer.id
    ).outerjoin(
        CallMetrics, CallSession.id == CallMetrics.call_session_id
    )
    
    # Filtering
    if organisation_id:
        query = query.where(CallSession.organisation_id == organisation_id)
        
    if start_date:
        query = query.where(CallSession.created_at >= start_date)
    if end_date:
        query = query.where(CallSession.created_at <= end_date)
        
    # Order by newest first
    query = query.order_by(desc(CallSession.created_at)).limit(500)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Pre-fetch organisations and companies for mapping
    org_result = await db.execute(select(Organisation))
    all_orgs = {o.id: o.name for o in org_result.scalars().all()}
    
    comp_result = await db.execute(select(Company))
    all_comps = comp_result.scalars().all()
    
    # Map phone to company name logic (reuse from company_calls.py)
    phone_to_company = {}
    for c in all_comps:
        if c.phone:
            phone_to_company[c.phone.lstrip('+')[-10:]] = c.name
        if c.secondary_phone:
            phone_to_company[c.secondary_phone.lstrip('+')[-10:]] = c.name

    formatted_logs = []
    
    for session, summary, farmer, metrics in rows:
        import json
        key_recs = summary.key_recommendations if summary and summary.key_recommendations else []
        if isinstance(key_recs, str):
            try:
                key_recs = json.loads(key_recs)
            except:
                key_recs = [key_recs]
                
        # Phone number based on direction
        farmer_phone = session.from_phone if session.call_direction == 'inbound' else session.to_phone
        company_phone = session.to_phone if session.call_direction == 'inbound' else session.from_phone
        
        company_name = "Unknown Company"
        if company_phone:
            clean_cp = company_phone.lstrip('+')[-10:]
            company_name = phone_to_company.get(clean_cp, "Unknown Company")
        
        # Filter by company_id if provided (client-side of this loop for simplicity given the mapping logic)
        if company_id:
            target_comp = next((c for c in all_comps if c.id == company_id), None)
            if target_comp and company_name != target_comp.name:
                continue

        satisfaction = "Pending"
        if metrics and metrics.farmer_satisfaction:
            if metrics.farmer_satisfaction >= 4:
                satisfaction = "Satisfied"
            elif metrics.farmer_satisfaction <= 2:
                satisfaction = "Not Satisfied"
        
        formatted_logs.append({
            "id": session.id,
            "session_id": session.session_id,
            "farmer_phone": farmer_phone or session.phone_number,
            "farmer_name": farmer.name if farmer else "Unknown Farmer",
            "organisation_name": all_orgs.get(session.organisation_id, "Unknown Organisation"),
            "company_name": company_name,
            "call_direction": session.call_direction,
            "status": session.status.value if session.status else "COMPLETED",
            "duration": session.duration_seconds,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "target_crop": (farmer.crop_type if farmer else "Unknown") or "Unknown", 
            "suggested_products": summary.products_mentioned if summary else [],
            "satisfaction": satisfaction, 
            "key_recommendations": key_recs,
            "summary_text": summary.summary_text_english if summary else ""
        })
        
    return formatted_logs


# ===== Platform Config Management =====

@router.get("/config")
async def get_platform_config(
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get current platform configuration"""
    result = await db.execute(select(PlatformConfig).limit(1))
    config = result.scalar_one_or_none()
    
    if not config:
        # Return default config
        return {
            "ai_confidence_threshold": 70,
            "max_call_duration_minutes": 15,
            "default_language": "hi",
            "stt_provider": "google",
            "tts_provider": "google",
            "llm_model": "gpt-4o",
            "embedding_model": "openai",
            "rag_strictness_level": "medium",
            "rag_min_confidence": 60,
            "force_kb_approval": True,
            "enable_call_recording": True,
            "enable_auto_escalation": True,
            "trial_duration_days": 14,
            "max_concurrent_calls": 100,
            "updated_at": None
        }
    
    return {
        "ai_confidence_threshold": config.ai_confidence_threshold,
        "max_call_duration_minutes": config.max_call_duration_minutes,
        "default_language": config.default_language,
        "stt_provider": config.stt_provider,
        "tts_provider": config.tts_provider,
        "llm_model": config.llm_model,
        "embedding_model": "google" if config.llm_model == "gemini" else "openai",
        "rag_strictness_level": config.rag_strictness_level,
        "rag_min_confidence": config.rag_min_confidence,
        "force_kb_approval": config.force_kb_approval,
        "enable_call_recording": config.enable_call_recording,
        "enable_auto_escalation": config.enable_auto_escalation,
        "trial_duration_days": config.trial_duration_days,
        "max_concurrent_calls": config.max_concurrent_calls,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None
    }


@router.put("/config")
async def update_platform_config(
    config_data: PlatformConfigUpdate,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Update platform configuration"""
    user = current_user
    
    result = await db.execute(select(PlatformConfig).limit(1))
    config = result.scalar_one_or_none()
    
    old_value = None
    if config:
        old_value = {
            "ai_confidence_threshold": config.ai_confidence_threshold,
            "rag_strictness_level": config.rag_strictness_level,
            "llm_model": config.llm_model
        }
        
        # Update existing config
        for field, value in config_data.dict(exclude_unset=True).items():
            setattr(config, field, value)
        config.updated_at = datetime.now(timezone.utc)
    else:
        # Create new config
        config = PlatformConfig(**config_data.dict(exclude_unset=True))
        config.updated_at = datetime.now(timezone.utc)
        db.add(config)
    
    await db.commit()
    await db.refresh(config)
    
    # Create audit log
    await create_audit_log(
        db=db,
        user=user,
        action_type="config_update",
        action_category="platform",
        description=f"Updated platform AI/RAG configuration",
        entity_type="platform_config",
        entity_id=config.id,
        old_value=old_value,
        new_value=config_data.dict(exclude_unset=True),
        severity="warning",
        request=request
    )
    
    return {
        "message": "Platform configuration updated successfully",
        "config": {
            "ai_confidence_threshold": config.ai_confidence_threshold,
            "max_call_duration_minutes": config.max_call_duration_minutes,
            "default_language": config.default_language,
            "stt_provider": config.stt_provider,
            "tts_provider": config.tts_provider,
            "llm_model": config.llm_model,
            "rag_strictness_level": config.rag_strictness_level,
            "rag_min_confidence": config.rag_min_confidence,
            "force_kb_approval": config.force_kb_approval,
            "enable_call_recording": config.enable_call_recording,
            "enable_auto_escalation": config.enable_auto_escalation,
            "trial_duration_days": config.trial_duration_days,
            "max_concurrent_calls": config.max_concurrent_calls,
            "updated_at": config.updated_at.isoformat()
        }
    }

@router.get("/users")
async def get_users(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, request: Request, current_user: dict = Depends(get_current_super_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    username = user.username
    user_role = user.role
    
    # Save IDs before any delete (FK SET NULL would clear these)
    org_id_to_delete = user.organisation_id if user.role == "organisation" else None
    company_id_to_delete = user.company_id if user.role == "company" else None
    # Also capture the org_id for company users (company belongs to an org)
    company_org_id = user.organisation_id if user.role == "company" else None
    
    # Step 1: Detach user from org/company to avoid FK conflicts
    user.organisation_id = None
    user.company_id = None
    await db.flush()
    
    # Step 2: Delete the user
    await db.delete(user)
    await db.flush()
    
    # Step 3: Delete the organisation (and its cascaded companies, brands, products)
    if org_id_to_delete:
        # Check if any OTHER users still belong to this organisation
        other_users = await db.execute(
            select(User).where(User.organisation_id == org_id_to_delete)
        )
        remaining_users = other_users.scalars().all()
        
        if not remaining_users:
            # No other users, safe to delete the organisation
            org_result = await db.execute(select(Organisation).where(Organisation.id == org_id_to_delete))
            org = org_result.scalar_one_or_none()
            if org:
                await db.delete(org)
                logger.info(f"Cascade deleted organisation '{org.name}' (id={org_id_to_delete}) with user '{username}'")
        else:
            logger.info(f"Organisation id={org_id_to_delete} kept — {len(remaining_users)} other user(s) still linked")
    
    # Step 4: Delete the company (and its cascaded brands, products)
    if company_id_to_delete:
        # Check if any OTHER users still belong to this company
        other_users = await db.execute(
            select(User).where(User.company_id == company_id_to_delete)
        )
        remaining_users = other_users.scalars().all()
        
        if not remaining_users:
            company_result = await db.execute(select(Company).where(Company.id == company_id_to_delete))
            company = company_result.scalar_one_or_none()
            if company:
                await db.delete(company)
                logger.info(f"Cascade deleted company '{company.name}' (id={company_id_to_delete}) with user '{username}'")
        else:
            logger.info(f"Company id={company_id_to_delete} kept — {len(remaining_users)} other user(s) still linked")
    
    await db.commit()
    
    # Audit log (after commit so admin user is still valid)
    current_user_obj = await db.execute(select(User).where(User.username == current_user["username"]))
    admin_obj = current_user_obj.scalar_one_or_none()
    if admin_obj:
        await create_audit_log(
            db=db,
            user=admin_obj,
            action_type="user_delete",
            action_category="user",
            description=f"Deleted user: {username} (role: {user_role})" + 
                (f" and organisation id={org_id_to_delete}" if org_id_to_delete else "") +
                (f" and company id={company_id_to_delete}" if company_id_to_delete else ""),
            entity_type="user",
            entity_id=user_id,
            old_value={"username": username, "role": user_role},
            severity="warning",
            request=request,
        )
        
    return {"success": True, "message": f"User '{username}' and all related data deleted successfully"}

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    request: Request,
    current_user: dict = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)):
    
    body = await request.json()
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    old_values = {"email": user.email, "full_name": user.full_name, "role": user.role, "status": user.status}
    
    if "email" in body:
        user.email = body["email"]
        user.username = body["email"]
    if "full_name" in body:
        user.full_name = body["full_name"]
    if "role" in body:
        user.role = body["role"]
    if "status" in body:
        user.status = body["status"]
    elif "is_active" in body:
        # Backward compatibility: convert boolean is_active to status string
        user.status = "active" if body["is_active"] else "inactive"
        
    await db.commit()
    return {"success": True, "message": "User updated"}
    
