from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from typing import List, Optional
from datetime import datetime
import logging

from db.session import get_db
from api.routes.auth import get_current_user
from db.models.company import Company
from db.models.call_session import CallSession
from db.models.call_summary import CallSummary
from db.models.farmer import Farmer
from db.models.call_metrics import CallMetrics

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/calls")
async def get_company_calls(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    filter_company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all call logs. For organisation admins, it fetches all calls and maps them to companies via phone numbers.
    Supports filtering by specific company_id using filter_company_id.
    """
    company_id = current_user.get("company_id")
    org_id = current_user.get("organisation_id")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="User not associated with any organisation")
        
    query = select(CallSession, CallSummary, Farmer, CallMetrics).outerjoin(
        CallSummary, CallSession.id == CallSummary.call_session_id
    ).outerjoin(
        Farmer, CallSession.farmer_id == Farmer.id
    ).outerjoin(
        CallMetrics, CallSession.id == CallMetrics.call_session_id
    )
    
    # Pre-fetch all companies for this org to map phone numbers back to company names
    companies_result = await db.execute(select(Company).where(Company.organisation_id == org_id))
    all_companies = companies_result.scalars().all()
    
    phone_to_company = {}
    for c in all_companies:
        if c.phone:
            phone_to_company[c.phone.lstrip('+')[-10:]] = c.name
        if c.secondary_phone:
            phone_to_company[c.secondary_phone.lstrip('+')[-10:]] = c.name
            
    target_company_id = company_id or filter_company_id
    
    if target_company_id:
        target_company = next((c for c in all_companies if c.id == target_company_id), None)
        
        if not target_company:
            # Maybe the company belongs to another org, or doesn't exist
            return []
            
        # Get phone values to match against
        phones_to_match = []
        if target_company.phone:
            phones_to_match.append(target_company.phone)
            clean_phone = target_company.phone.lstrip('+')
            phones_to_match.append(f"%{clean_phone[-10:]}") 
        if target_company.secondary_phone:
            clean_sec = target_company.secondary_phone.lstrip('+')
            phones_to_match.append(f"%{clean_sec[-10:]}")
            
        if not phones_to_match:
            return [] # Company has no phone, can't have calls
            
        # Build wildcard OR conditions for both from_phone and to_phone
        phone_conditions = []
        for p in phones_to_match:
            phone_conditions.append(CallSession.to_phone.like(p))
            phone_conditions.append(CallSession.from_phone.like(p))
            
        query = query.where(
            and_(
                CallSession.organisation_id == org_id,
                or_(*phone_conditions)
            )
        )
    else:
        # If user has no company_id and no filter, show all org calls
        query = query.where(CallSession.organisation_id == org_id)
        
    # Date filtering
    if start_date:
        query = query.where(CallSession.created_at >= start_date)
    if end_date:
        query = query.where(CallSession.created_at <= end_date)
        
    # Order by newest first limit
    query = query.order_by(desc(CallSession.created_at)).limit(500)
    
    result = await db.execute(query)
    rows = result.all()
    
    formatted_logs = []
    
    for session, summary, farmer, metrics in rows:
        try:
            key_recs = summary.key_recommendations if summary and summary.key_recommendations else []
            if isinstance(key_recs, str):
                import json
                try:
                    key_recs = json.loads(key_recs)
                except:
                    key_recs = [key_recs]
                    
            # Phone number based on direction
            farmer_phone = session.from_phone if session.call_direction == 'inbound' else session.to_phone
            company_phone = session.to_phone if session.call_direction == 'inbound' else session.from_phone
            
            # Try to match company from both phones (to handle admin test calls)
            company_name = "Unknown Company"
            cp_to = session.to_phone.lstrip('+')[-10:] if session.to_phone else ""
            cp_from = session.from_phone.lstrip('+')[-10:] if session.from_phone else ""
            
            # Priority: 
            # 1. For inbound, check to_phone first (the VN)
            # 2. For outbound, check from_phone first (the VN)
            # 3. Fallback to the other side
            if session.call_direction == 'inbound':
                company_name = phone_to_company.get(cp_to) or phone_to_company.get(cp_from)
            else:
                company_name = phone_to_company.get(cp_from) or phone_to_company.get(cp_to)
            
            # Strategy: If org has only one company, fallback to that company name
            if not company_name and len(all_companies) == 1:
                company_name = all_companies[0].name
            
            if not company_name:
                company_name = "Unknown Company"
            
            satisfaction = "Pending"
            if metrics and metrics.farmer_satisfaction:
                if metrics.farmer_satisfaction >= 4:
                    satisfaction = "Satisfied"
                elif metrics.farmer_satisfaction <= 2:
                    satisfaction = "Not Satisfied"
            
            # Safe status access handling both Enum and string
            status_val = session.status
            if hasattr(status_val, "value"):
                status_val = status_val.value
            elif status_val is None:
                status_val = "COMPLETED"

            formatted_logs.append({
                "id": session.id,
                "session_id": session.session_id,
                "farmer_phone": farmer_phone or session.phone_number,
                "farmer_name": farmer.name if farmer else "Unknown Farmer",
                "company_name": company_name,
                "call_direction": session.call_direction,
                "status": status_val,
                "duration": session.duration_seconds,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "target_crop": (summary.target_crop if summary and summary.target_crop else (farmer.crop_type if farmer else "Unknown")) or "Unknown", 
                "suggested_products": summary.products_mentioned if summary else [],
                "satisfaction": satisfaction, 
                "key_recommendations": key_recs,
                "summary_text": summary.summary_text_english if summary else ""
            })
        except Exception as e:
            logger.error(f"Error formatting call log row for session {session.id if session else 'unknown'}: {e}")
            continue
        
    return formatted_logs
