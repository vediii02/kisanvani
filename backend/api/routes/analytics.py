"""
Analytics API Routes
Dashboard and reporting endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from api.deps import get_db
from services.analytics_service import analytics_service

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    organisation_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive dashboard statistics
    
    Query params:
    - organisation_id: Filter by organisation
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    """
    # Parse dates
    dt_from = datetime.fromisoformat(date_from) if date_from else None
    dt_to = datetime.fromisoformat(date_to) if date_to else None
    
    stats = await analytics_service.get_dashboard_stats(
        db,
        organisation_id=organisation_id,
        date_from=dt_from,
        date_to=dt_to
    )
    
    return stats


@router.get("/calls")
async def get_call_analytics(
    organisation_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed call analytics"""
    dt_from = datetime.fromisoformat(date_from) if date_from else None
    dt_to = datetime.fromisoformat(date_to) if date_to else None
    
    analytics = await analytics_service.get_call_analytics(
        db,
        organisation_id=organisation_id,
        date_from=dt_from,
        date_to=dt_to
    )
    
    return analytics


@router.get("/farmers")
async def get_farmer_analytics(
    organisation_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get farmer engagement analytics"""
    analytics = await analytics_service.get_farmer_analytics(
        db,
        organisation_id=organisation_id
    )
    
    return analytics


@router.get("/report/{report_type}")
async def generate_report(
    report_type: str,
    organisation_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate comprehensive report
    
    Report types: daily, weekly, monthly, custom
    """
    dt_from = datetime.fromisoformat(date_from) if date_from else None
    dt_to = datetime.fromisoformat(date_to) if date_to else None
    
    report = await analytics_service.generate_report(
        db,
        report_type=report_type,
        organisation_id=organisation_id,
        date_from=dt_from,
        date_to=dt_to
    )
    
    return report
