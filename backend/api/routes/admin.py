from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.session import get_db
from db.models.call_session import CallSession, CallStatus
from db.models.case import Case, CaseStatus
from db.models.farmer import Farmer, FarmerStatus
from db.models.escalation import Escalation, EscalationStatus
from db.models.kb_entry import KBEntry
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
@router.get("/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    total_calls_result = await db.execute(select(func.count(CallSession.id)))
    total_calls = total_calls_result.scalar() 
    
    active_calls_result = await db.execute(
        select(func.count(CallSession.id)).where(CallSession.status == CallStatus.ACTIVE)
    )
    active_calls = active_calls_result.scalar()
    
    total_farmers_result = await db.execute(select(func.count(Farmer.id)))
    total_farmers = total_farmers_result.scalar()
    
    total_cases_result = await db.execute(select(func.count(Case.id)))
    total_cases = total_cases_result.scalar()
    
    pending_escalations_result = await db.execute(
        select(func.count(Escalation.id)).where(Escalation.status == EscalationStatus.PENDING)
    )
    pending_escalations = pending_escalations_result.scalar()
    
    kb_entries_result = await db.execute(
        select(func.count(KBEntry.id)).where(KBEntry.is_approved == True)
    )
    kb_entries = kb_entries_result.scalar()
    
    return {
        'total_calls': total_calls,
        'active_calls': active_calls,
        'total_farmers': total_farmers,
        'total_cases': total_cases,
        'pending_escalations': pending_escalations,
        'approved_kb_entries': kb_entries
    }

@router.get("/farmers")
async def get_all_farmers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Farmer).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/escalations")
async def get_escalations(
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Escalation)
    if status:
        query = query.where(Escalation.status == status)
    
    result = await db.execute(query)
    return result.scalars().all()