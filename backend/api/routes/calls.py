from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from db.models.call_session import CallSession
from db.models.case import Case
from db.models.advisory import Advisory
from typing import List

router = APIRouter(prefix="/calls", tags=["calls"])

@router.get("")
async def get_calls(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get all calls - same as /history but at root path"""
    result = await db.execute(
        select(CallSession).order_by(CallSession.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/history")
async def get_call_history(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CallSession).order_by(CallSession.start_time.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/{session_id}/cases")
async def get_session_cases(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CallSession).where(CallSession.session_id == session_id)
    )
    call_session = result.scalar_one_or_none()
    if not call_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    cases_result = await db.execute(
        select(Case).where(Case.session_id == call_session.id)
    )
    return cases_result.scalars().all()

@router.get("/cases/{case_id}/advisory")
async def get_case_advisory(
    case_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Advisory).where(Advisory.case_id == case_id)
    )
    advisory = result.scalar_one_or_none()
    if not advisory:
        raise HTTPException(status_code=404, detail="Advisory not found")
    return advisory