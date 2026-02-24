"""Call flow state management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime

from api.deps import get_db
from core.auth import get_current_user
from db.models.user import User
from db.models.call_session import CallSession
from db.models.call_state import CallState, StateType
from voice.state_machine import CallFlowManager, StateMachine


router = APIRouter()


# Schemas
class IncomingCallRequest(BaseModel):
    from_phone: str = Field(..., description="Farmer's phone number")
    to_phone: str = Field(..., description="Organisation's phone number")
    exotel_call_sid: Optional[str] = Field(None, description="Exotel call SID")


class IncomingCallResponse(BaseModel):
    call_session_id: int
    organisation_id: int
    organisation_name: str
    current_state: str
    message: str
    welcome_message: Optional[str] = None
    welcome_audio_url: Optional[str] = None


class GreetingResponse(BaseModel):
    consent_given: bool
    farmer_name: Optional[str] = None


class StateTransitionRequest(BaseModel):
    target_state: str
    state_data: Optional[Dict] = None


class StateTransitionResponse(BaseModel):
    call_session_id: int
    previous_state: Optional[str]
    current_state: str
    state_data: Dict
    timestamp: datetime


class CallStatusResponse(BaseModel):
    call_session_id: int
    current_state: Optional[str]
    current_state_data: Dict
    states_visited: List[str]
    total_duration_seconds: float
    is_active: bool


# Endpoints

@router.post("/incoming", response_model=IncomingCallResponse)
async def handle_incoming_call(
    request: IncomingCallRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming call from Exotel
    Webhook endpoint called when farmer dials organisation number
    """
    from db.models.organisation_phone import OrganisationPhoneNumber
    from db.models.organisation import Organisation
    
    # Lookup organisation by phone number
    result = await db.execute(
        select(OrganisationPhoneNumber)
        .where(
            OrganisationPhoneNumber.phone_number == request.to_phone,
            OrganisationPhoneNumber.status == "active"
        )
    )
    org_phone = result.scalar_one_or_none()
    
    if not org_phone:
        raise HTTPException(
            status_code=404,
            detail=f"No organisation found for phone number {request.to_phone}"
        )
    
    # Get organisation details
    organisation = await db.get(Organisation, org_phone.organisation_id)
    
    # Create call session
    import uuid
    call_session = CallSession(
        session_id=str(uuid.uuid4()),
        phone_number=request.from_phone,
        from_phone=request.from_phone,
        to_phone=request.to_phone,
        exotel_call_sid=request.exotel_call_sid,
        call_direction='inbound',
        status='active'
    )
    
    db.add(call_session)
    await db.commit()
    await db.refresh(call_session)
    
    # Initialize call flow
    flow_manager = CallFlowManager(db)
    await flow_manager.start_call(
        call_session.id,
        request.from_phone,
        request.to_phone
    )
    
    # Generate welcome audio
    from services.welcome_service import welcome_service
    try:
        audio_bytes, filename = await welcome_service.create_welcome_audio(
            org_name=organisation.name,
            session_id=call_session.id
        )
        welcome_message = welcome_service.generate_welcome_message(organisation.name)
        welcome_audio_url = f"/api/call-flow/audio/{filename}"
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to generate welcome audio: {e}")
        welcome_message = None
        welcome_audio_url = None
    
    return IncomingCallResponse(
        call_session_id=call_session.id,
        organisation_id=organisation.id,
        organisation_name=organisation.name,
        current_state="GREETING",
        message=f"Call routed to {organisation.name}",
        welcome_message=welcome_message,
        welcome_audio_url=welcome_audio_url
    )


@router.post("/{call_session_id}/greeting", response_model=StateTransitionResponse)
async def handle_greeting_response(
    call_session_id: int,
    response: GreetingResponse,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle farmer's response to greeting
    Farmer either gives consent or declines
    """
    # Verify call exists
    call_session = await db.get(CallSession, call_session_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    # Get current state
    state_machine = StateMachine(db)
    current_state = await state_machine.get_current_state(call_session_id)
    previous_state_name = current_state.state.value if current_state else None
    
    # Handle greeting response
    flow_manager = CallFlowManager(db)
    await flow_manager.handle_greeting_response(
        call_session_id,
        response.consent_given,
        response.farmer_name
    )
    
    # Get new state
    new_state = await state_machine.get_current_state(call_session_id)
    
    return StateTransitionResponse(
        call_session_id=call_session_id,
        previous_state=previous_state_name,
        current_state=new_state.state.value,
        state_data=new_state.state_data,
        timestamp=new_state.entered_at
    )


@router.get("/{call_session_id}/state", response_model=CallStatusResponse)
async def get_call_state(
    call_session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current call state and flow status
    Used by frontend for monitoring
    """
    # Verify call exists
    call_session = await db.get(CallSession, call_session_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    # Get call status
    flow_manager = CallFlowManager(db)
    status = await flow_manager.get_call_status(call_session_id)
    
    return CallStatusResponse(
        call_session_id=call_session_id,
        **status
    )


@router.post("/{call_session_id}/transition", response_model=StateTransitionResponse)
async def transition_state(
    call_session_id: int,
    request: StateTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manual state transition (for testing or expert override)
    Requires authentication
    """
    # Verify call exists
    call_session = await db.get(CallSession, call_session_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    # Validate state
    try:
        target_state = StateType(request.target_state.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state: {request.target_state}. Valid states: {[s.value for s in StateType]}"
        )
    
    # Get current state
    state_machine = StateMachine(db)
    current_state = await state_machine.get_current_state(call_session_id)
    previous_state_name = current_state.state.value if current_state else None
    
    # Transition
    try:
        new_state = await state_machine.transition_to(
            call_session_id,
            target_state,
            request.state_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return StateTransitionResponse(
        call_session_id=call_session_id,
        previous_state=previous_state_name,
        current_state=new_state.state.value,
        state_data=new_state.state_data,
        timestamp=new_state.entered_at
    )


@router.post("/{call_session_id}/end")
async def end_call(
    call_session_id: int,
    reason: Optional[str] = "completed",
    db: AsyncSession = Depends(get_db)
):
    """
    Force end a call from any state
    """
    # Verify call exists
    call_session = await db.get(CallSession, call_session_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    # End call
    flow_manager = CallFlowManager(db)
    await flow_manager.end_call(call_session_id, reason)
    
    # Update call session status
    call_session.status = 'completed'
    call_session.end_time = datetime.utcnow()
    await db.commit()
    
    return {
        "message": "Call ended",
        "call_session_id": call_session_id,
        "reason": reason
    }


@router.get("/{call_session_id}/history", response_model=List[Dict])
async def get_state_history(
    call_session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete state history for a call
    Useful for debugging and analytics
    """
    # Verify call exists
    call_session = await db.get(CallSession, call_session_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    # Get state history
    state_machine = StateMachine(db)
    states = await state_machine.get_state_history(call_session_id)
    
    # Calculate durations
    history = []
    for state in states:
        duration = await state_machine.get_time_in_state(state)
        history.append({
            "state": state.state.value,
            "entered_at": state.entered_at.isoformat(),
            "exited_at": state.exited_at.isoformat() if state.exited_at else None,
            "duration_seconds": duration,
            "state_data": state.state_data
        })
    
    return history

@router.get("/audio/{filename}")
async def serve_audio_file(filename: str):
    """
    Serve audio files for playback
    Used to stream welcome messages and responses to the caller
    """
    from fastapi.responses import FileResponse
    import os
    
    audio_dir = "/tmp/audio"
    filepath = os.path.join(audio_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        filepath,
        media_type="audio/wav",
        headers={
            "Content-Disposition": f"inline; filename={filename}"
        }
    )

class NextQuestionRequest(BaseModel):
    call_session_id: int
    current_step: int = 0
    context: Optional[Dict] = None


class NextQuestionResponse(BaseModel):
    question_type: str
    question_text: str
    question_audio_url: Optional[str] = None
    current_step: int
    progress: Dict


@router.post("/next-question", response_model=NextQuestionResponse)
async def get_next_question(
    request: NextQuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get next question in the conversation flow
    Automatically generates audio for the question
    """
    from services.welcome_service import conversation_flow, welcome_service
    
    # Verify call session exists
    call_session = await db.get(CallSession, request.call_session_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    # Get next question based on current step
    if request.context:
        # If context provided (like crop name, area), use it
        question_type = conversation_flow.FLOW_SEQUENCE[request.current_step] if request.current_step < len(conversation_flow.FLOW_SEQUENCE) else "complete"
        question_text = conversation_flow.get_question_with_context(question_type, request.context)
    else:
        # Get standard next question
        question_type, question_text = conversation_flow.get_next_question(request.current_step)
    
    # Get progress
    progress = conversation_flow.get_progress(request.current_step + 1)
    
    # Generate audio for the question
    audio_url = None
    if question_type != "complete":
        try:
            audio_bytes, filename = await welcome_service.create_question_audio(
                question_type,
                session_id=request.call_session_id
            )
            audio_url = f"/api/call-flow/audio/{filename}"
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to generate question audio: {e}")
    
    return NextQuestionResponse(
        question_type=question_type,
        question_text=question_text,
        question_audio_url=audio_url,
        current_step=request.current_step + 1,
        progress=progress
    )


class SaveAnswerRequest(BaseModel):
    call_session_id: int
    question_type: str
    question_text: str
    answer_text: str
    current_step: int


class SaveAnswerResponse(BaseModel):
    success: bool
    message: str
    answers_saved: int
    context_data: Dict


@router.post("/save-answer", response_model=SaveAnswerResponse)
async def save_answer(
    request: SaveAnswerRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Save farmer's answer to a question
    Updates call_states with conversation context
    """
    # Verify call session exists
    call_session = await db.get(CallSession, request.call_session_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    # Get current state or create new one
    result = await db.execute(
        select(CallState)
        .where(CallState.call_session_id == request.call_session_id)
        .where(CallState.exited_at.is_(None))
        .order_by(CallState.entered_at.desc())
    )
    call_state = result.scalar_one_or_none()
    
    if not call_state:
        # Create new state for storing conversation
        call_state = CallState(
            call_session_id=request.call_session_id,
            state=StateType.PROFILING,
            state_data={"answers": {}, "current_step": 0}
        )
        db.add(call_state)
    
    # Update state_data with the answer
    if not call_state.state_data:
        call_state.state_data = {"answers": {}}
    
    if "answers" not in call_state.state_data:
        call_state.state_data["answers"] = {}
    
    # Store the answer
    call_state.state_data["answers"][request.question_type] = {
        "question": request.question_text,
        "answer": request.answer_text,
        "step": request.current_step,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    call_state.state_data["current_step"] = request.current_step
    call_state.state_data["last_updated"] = datetime.utcnow().isoformat()
    
    # Mark as modified for SQLAlchemy to detect change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(call_state, "state_data")
    
    await db.commit()
    await db.refresh(call_state)
    
    return SaveAnswerResponse(
        success=True,
        message=f"Answer saved for {request.question_type}",
        answers_saved=len(call_state.state_data.get("answers", {})),
        context_data=call_state.state_data.get("answers", {})
    )


class GetConversationResponse(BaseModel):
    call_session_id: int
    from_phone: str
    to_phone: str
    organisation_name: str
    current_state: str
    current_step: int
    answers: Dict
    progress: Dict
    created_at: str


@router.get("/{call_session_id}/conversation", response_model=GetConversationResponse)
async def get_conversation(
    call_session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete conversation history for a call session
    """
    from services.welcome_service import conversation_flow
    
    # Get call session
    call_session = await db.get(CallSession, call_session_id)
    if not call_session:
        raise HTTPException(status_code=404, detail="Call session not found")
    
    # Get organisation by phone number
    from db.models.organisation import Organisation
    from db.models.organisation_phone import OrganisationPhoneNumber
    
    result = await db.execute(
        select(Organisation)
        .join(OrganisationPhoneNumber)
        .where(OrganisationPhoneNumber.phone_number == call_session.to_phone)
    )
    organisation = result.scalar_one_or_none()
    
    # Get current state
    result = await db.execute(
        select(CallState)
        .where(CallState.call_session_id == call_session_id)
        .where(CallState.exited_at.is_(None))
        .order_by(CallState.entered_at.desc())
    )
    call_state = result.scalar_one_or_none()
    
    answers = {}
    current_step = 0
    
    if call_state and call_state.state_data:
        answers = call_state.state_data.get("answers", {})
        current_step = call_state.state_data.get("current_step", 0)
    
    # Calculate progress
    progress = conversation_flow.get_progress(current_step)
    
    return GetConversationResponse(
        call_session_id=call_session.id,
        from_phone=call_session.from_phone,
        to_phone=call_session.to_phone,
        organisation_name=organisation.name if organisation else "Unknown",
        current_state=call_state.state.value if call_state else "UNKNOWN",
        current_step=current_step,
        answers=answers,
        progress=progress,
        created_at=call_session.created_at.isoformat()
    )
