from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from core.auth import get_current_user
from db.session import get_db
from db.models.company import Company
from db.models.brand import Brand
from db.models.product import Product
from db.models.call_session import CallSession
from db.models.call_summary import CallSummary
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CompanyStatsResponse(BaseModel):
    totalBrands: int
    activeBrands: int
    inactiveBrands: int
    totalProducts: int
    activeProducts: int
    inactiveProducts: int
    totalCalls: int
    recentQueries: int

@router.get("/stats", response_model=CompanyStatsResponse)
async def get_company_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics for the current user's company"""
    if current_user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Access denied. Company role required.")
    
    company_id = current_user.get("company_id")
    org_id = current_user.get("organisation_id")
    
    if not company_id:
        raise HTTPException(status_code=404, detail="Company not found for user.")
    
    # Get company details to get phone numbers
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")
    
    # Check if this is the only company in the organisation
    all_companies_result = await db.execute(
        select(func.count(Company.id)).where(Company.organisation_id == org_id)
    )
    is_single_company = all_companies_result.scalar() == 1
    
    # 1. Brand stats
    brand_total = await db.execute(select(func.count(Brand.id)).where(Brand.company_id == company_id))
    brand_active = await db.execute(select(func.count(Brand.id)).where(Brand.company_id == company_id, Brand.is_active == True))
    
    total_brands = brand_total.scalar() or 0
    active_brands = brand_active.scalar() or 0
    
    # 2. Product stats
    product_total = await db.execute(select(func.count(Product.id)).where(Product.company_id == company_id))
    product_active = await db.execute(select(func.count(Product.id)).where(Product.company_id == company_id, Product.is_active == True))
    
    total_products = product_total.scalar() or 0
    active_products = product_active.scalar() or 0
    
    # 3. Call stats
    total_calls = 0
    total_queries = 0

    if is_single_company:
        # If single company, attribute all org calls to it
        calls_query = select(func.count(CallSession.id)).where(CallSession.organisation_id == org_id)
        calls_result = await db.execute(calls_query)
        total_calls = calls_result.scalar() or 0
        
        queries_query = select(func.count(CallSummary.id)).join(
            CallSession, CallSession.id == CallSummary.call_session_id
        ).where(CallSession.organisation_id == org_id)
        queries_result = await db.execute(queries_query)
        total_queries = queries_result.scalar() or 0
    else:
        # Identifty company phones for filtering
        phones_to_match = []
        if company.phone:
            phones_to_match.append(company.phone)
            clean_phone = company.phone.lstrip('+')
            phones_to_match.append(f"%{clean_phone[-10:]}") 
        if company.secondary_phone:
            clean_sec = company.secondary_phone.lstrip('+')
            phones_to_match.append(f"%{clean_sec[-10:]}")
            
        if phones_to_match:
            phone_conditions = []
            for p in phones_to_match:
                phone_conditions.append(CallSession.to_phone.like(p))
                phone_conditions.append(CallSession.from_phone.like(p))
                
            # Count calls
            calls_query = select(func.count(CallSession.id)).where(
                CallSession.organisation_id == org_id,
                or_(*phone_conditions)
            )
            calls_result = await db.execute(calls_query)
            total_calls = calls_result.scalar() or 0
            
            # Count queries (associated call summaries)
            queries_query = select(func.count(CallSummary.id)).join(
                CallSession, CallSession.id == CallSummary.call_session_id
            ).where(
                CallSession.organisation_id == org_id,
                or_(*phone_conditions)
            )
            queries_result = await db.execute(queries_query)
            total_queries = queries_result.scalar() or 0
    
    return CompanyStatsResponse(
        totalBrands=total_brands,
        activeBrands=active_brands,
        inactiveBrands=total_brands - active_brands,
        totalProducts=total_products,
        activeProducts=active_products,
        inactiveProducts=total_products - active_products,
        totalCalls=total_calls,
        recentQueries=total_queries
    )
