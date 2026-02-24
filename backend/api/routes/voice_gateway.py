from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from db.models.call_session import CallSession, CallStatus
from db.models.farmer import Farmer
from db.models.case import Case, CaseStatus
from db.models.advisory import Advisory
from voice.session_manager import session_manager
from voice.flow_manager import flow_manager
from services.gemini_advisory_service import gemini_advisory_service as advisory_service
from services.escalation_service import escalation_service
from nlu.intent import detect_intent
from nlu.entity_extractor import extract_crop
from pydantic import BaseModel
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])

class SessionStartRequest(BaseModel):
    phone_number: str
    provider_name: str = "generic"
    provider_call_id: str = None

class SessionStartResponse(BaseModel):
    session_id: str
    message: str

@router.post("/session/start", response_model=SessionStartResponse)
async def start_voice_session(
    request: SessionStartRequest,
    db: AsyncSession = Depends(get_db)
):
    session_id = await session_manager.create_session(
        phone_number=request.phone_number,
        metadata={'provider': request.provider_name}
    )
    
    result = await db.execute(
        select(Farmer).where(Farmer.phone_number == request.phone_number)
    )
    farmer = result.scalar_one_or_none()
    
    if not farmer:
        farmer = Farmer(
            phone_number=request.phone_number,
            language='hi'
        )
        db.add(farmer)
        await db.commit()
        await db.refresh(farmer)
    
    call_session = CallSession(
        session_id=session_id,
        farmer_id=farmer.id,
        phone_number=request.phone_number,
        provider_name=request.provider_name,
        provider_call_id=request.provider_call_id,
        status=CallStatus.ACTIVE
    )
    db.add(call_session)
    await db.commit()
    
    logger.info(f"Started voice session {session_id} for {request.phone_number}")
    
    return SessionStartResponse(
        session_id=session_id,
        message="Session started successfully"
    )

@router.post("/session/{session_id}/process")
async def process_voice_input(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    session_data = await session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    mock_audio = b"mock_audio_data"
    transcribed_text = await flow_manager.process_audio(mock_audio)
    
    result = await db.execute(
        select(CallSession).where(CallSession.session_id == session_id)
    )
    call_session = result.scalar_one_or_none()
    
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found in DB")
    
    intent = detect_intent(transcribed_text)
    crop = extract_crop(transcribed_text)
    
    case = Case(
        session_id=call_session.id,
        farmer_id=call_session.farmer_id,
        problem_text=transcribed_text,
        problem_category=intent,
        crop_name=crop,
        status=CaseStatus.OPEN
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    advisory_result = await advisory_service.generate_advisory(transcribed_text, session_id)
    
    advisory = Advisory(
        case_id=case.id,
        advisory_text_hindi=advisory_result['advisory_text'],
        kb_entry_ids=','.join(map(str, advisory_result.get('kb_entries', []))),
        was_escalated=advisory_result['escalated']
    )
    db.add(advisory)
    
    if advisory_result['escalated']:
        await escalation_service.create_escalation(
            db=db,
            case_id=case.id,
            reason=advisory_result['reason'],
            confidence_score=str(advisory_result['confidence'])
        )
        case.status = CaseStatus.ESCALATED
    else:
        case.status = CaseStatus.RESOLVED
    
    case.confidence_score = str(advisory_result['confidence'])
    await db.commit()
    
    audio_response = await flow_manager.generate_audio_response(
        advisory_result['advisory_text'],
        language='hi'
    )
    
    return {
        'session_id': session_id,
        'case_id': case.id,
        'transcribed_text': transcribed_text,
        'advisory': advisory_result['advisory_text'],
        'confidence': advisory_result['confidence'],
        'escalated': advisory_result['escalated'],
        'audio_response': "[Audio data generated]"
    }

@router.post("/session/{session_id}/end")
async def end_voice_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    await session_manager.end_session(session_id)
    
    result = await db.execute(
        select(CallSession).where(CallSession.session_id == session_id)
    )
    call_session = result.scalar_one_or_none()
    
    if call_session:
        call_session.status = CallStatus.COMPLETED
        call_session.end_time = datetime.now(timezone.utc)
        if call_session.start_time:
            duration = (call_session.end_time - call_session.start_time).total_seconds()
            call_session.duration_seconds = int(duration)
        await db.commit()
    
    return {'message': 'Session ended', 'session_id': session_id}