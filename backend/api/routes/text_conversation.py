"""
Text Conversation API Routes
Handles text-based AI conversations with farmers
For testing and development before full voice integration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from db.session import get_db
from db.models.call_session import CallSession
from db.models.farmer import Farmer
from db.models.organisation import Organisation
from services.conversation_manager import conversation_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class StartConversationRequest(BaseModel):
    call_session_id: int


class StartConversationResponse(BaseModel):
    success: bool
    message: str
    session_id: int
    state: str
    suggestions: Optional[List[str]] = None


class SendMessageRequest(BaseModel):
    call_session_id: int
    message: str


class SendMessageResponse(BaseModel):
    success: bool
    message: str
    state: str
    context: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    confidence: Optional[float] = None


class ConversationHistoryResponse(BaseModel):
    success: bool
    call_session_id: int
    history: List[Dict[str, Any]]
    total_turns: int


@router.post("/start", response_model=StartConversationResponse)
async def start_text_conversation(
    request: StartConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new text-based conversation
    
    Returns greeting and initial prompts
    """
    try:
        # Verify call session exists
        result = await db.execute(
            select(CallSession).where(CallSession.id == request.call_session_id)
        )
        call_session = result.scalar_one_or_none()
        
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Get organisation info from to_phone in call session
        organisation_name = None
        if call_session.to_phone:
            org_result = await db.execute(
                select(Organisation).where(Organisation.primary_phone == call_session.to_phone)
            )
            org = org_result.scalar_one_or_none()
            if org:
                organisation_name = org.name
        
        # Start conversation
        result = await conversation_manager.start_conversation(
            db=db,
            call_session_id=request.call_session_id,
            organisation_name=organisation_name
        )
        
        return StartConversationResponse(
            success=result["success"],
            message=result["message"],
            session_id=request.call_session_id,
            state=result["state"],
            suggestions=result.get("suggestions")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a text message and get AI response
    
    This is the main conversation endpoint:
    1. Farmer sends text message
    2. System processes with NLU + RAG + LLM
    3. Returns intelligent response
    """
    try:
        # Verify call session exists
        result = await db.execute(
            select(CallSession).where(CallSession.id == request.call_session_id)
        )
        call_session = result.scalar_one_or_none()
        
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Don't reject empty messages here - let conversation_manager handle it
        # This allows for better Hindi responses and retry logic
        
        # Process message (handles empty/unclear messages internally)
        result = await conversation_manager.process_message(
            db=db,
            call_session_id=request.call_session_id,
            farmer_message=request.message.strip() if request.message else ""
        )
        
        return SendMessageResponse(
            success=result["success"],
            message=result["message"],
            state=result.get("state", "unknown"),
            context=result.get("context"),
            suggestions=result.get("suggestions"),
            confidence=result.get("confidence")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{call_session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    call_session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full conversation history for a session
    """
    try:
        # Verify call session exists
        result = await db.execute(
            select(CallSession).where(CallSession.id == call_session_id)
        )
        call_session = result.scalar_one_or_none()
        
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Get history
        history = conversation_manager.get_conversation_history(str(call_session_id))
        
        return ConversationHistoryResponse(
            success=True,
            call_session_id=call_session_id,
            history=history,
            total_turns=len(history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{call_session_id}")
async def clear_conversation_session(
    call_session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Clear conversation session (reset state)
    """
    try:
        conversation_manager.clear_session(str(call_session_id))
        
        return {
            "success": True,
            "message": "Conversation session cleared"
        }
        
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/quick")
async def quick_test_conversation(db: AsyncSession = Depends(get_db)):
    """
    Quick test endpoint - Creates test session and runs sample conversation
    For development/testing only
    """
    try:
        # Create test call session
        from db.models.call_session import CallStatus
        from datetime import datetime, timezone
        
        test_session = CallSession(
            session_id=f"test_{int(datetime.now().timestamp())}",
            farmer_id=1,  # Assumes farmer ID 1 exists
            phone_number="+919999999999",
            from_phone="+919999999999",
            to_phone="07314621863",
            status=CallStatus.ACTIVE,
            provider_name="test"
        )
        
        db.add(test_session)
        await db.commit()
        await db.refresh(test_session)
        
        # Start conversation
        start_result = await conversation_manager.start_conversation(
            db=db,
            call_session_id=test_session.id,
            organisation_name="Test Organisation"
        )
        
        # Send test message
        message_result = await conversation_manager.process_message(
            db=db,
            call_session_id=test_session.id,
            farmer_message="मेरी धान की फसल में कीड़े लग गए हैं"
        )
        
        return {
            "success": True,
            "test_session_id": test_session.id,
            "greeting": start_result["message"],
            "test_query": "मेरी धान की फसल में कीड़े लग गए हैं",
            "ai_response": message_result["message"],
            "state": message_result.get("state"),
            "context": message_result.get("context")
        }
        
    except Exception as e:
        logger.error(f"Test conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
