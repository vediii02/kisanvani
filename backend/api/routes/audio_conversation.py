"""
Audio Conversation API Routes
Handles voice-based AI conversations with farmers
Integrates STT (Speech-to-Text) + Text Conversation + TTS
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from db.session import get_db
from db.models.call_session import CallSession
from services.conversation_manager import conversation_manager
from services.stt_service import STTService
from services.tts_service import TTSService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class AudioMessageResponse(BaseModel):
    success: bool
    transcribed_text: str
    ai_response_text: str
    audio_url: str
    state: str
    confidence: Optional[float] = None


stt_service = STTService()
tts_service = TTSService()


@router.post("/audio/message/{call_session_id}", response_model=AudioMessageResponse)
async def send_audio_message(
    call_session_id: int,
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, OGG)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete audio conversation flow:
    1. Receive farmer's audio
    2. Convert to text (STT)
    3. Process with AI (NLU + RAG + LLM)
    4. Generate audio response (TTS)
    5. Return audio URL
    """
    try:
        # Verify call session
        result = await db.execute(
            select(CallSession).where(CallSession.id == call_session_id)
        )
        call_session = result.scalar_one_or_none()
        
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Step 1: Speech to Text
        audio_bytes = await audio.read()
        
        logger.info(f"Processing audio: {audio.filename}, size: {len(audio_bytes)} bytes")
        
        stt_result = await stt_service.transcribe_audio(
            audio_data=audio_bytes,
            language="hi"  # Hindi
        )
        
        if not stt_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=f"Speech recognition failed: {stt_result.get('error', 'Unknown error')}"
            )
        
        transcribed_text = stt_result.get("text", "")
        logger.info(f"Transcribed: {transcribed_text}")
        
        if not transcribed_text.strip():
            raise HTTPException(status_code=400, detail="Could not understand audio")
        
        # Step 2: Process with AI
        ai_result = await conversation_manager.process_message(
            db=db,
            call_session_id=call_session_id,
            farmer_message=transcribed_text
        )
        
        if not ai_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"AI processing failed: {ai_result.get('error', 'Unknown error')}"
            )
        
        ai_response_text = ai_result.get("message", "")
        logger.info(f"AI Response: {ai_response_text}")
        
        # Step 3: Text to Speech
        tts_result = await tts_service.synthesize_speech(
            text=ai_response_text,
            language="hi",
            session_id=str(call_session_id)
        )
        
        if not tts_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Speech synthesis failed: {tts_result.get('error', 'Unknown error')}"
            )
        
        audio_url = tts_result.get("audio_url", "")
        
        return AudioMessageResponse(
            success=True,
            transcribed_text=transcribed_text,
            ai_response_text=ai_response_text,
            audio_url=audio_url,
            state=ai_result.get("state", "unknown"),
            confidence=ai_result.get("confidence")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in audio conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio/streaming/{call_session_id}")
async def audio_streaming_conversation(
    call_session_id: int,
    audio_chunk: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Real-time streaming audio conversation (for future Exotel integration)
    Processes audio chunks in real-time
    """
    # TODO: Implement real-time streaming
    # For now, return not implemented
    raise HTTPException(
        status_code=501,
        detail="Streaming conversation not yet implemented. Use /audio/message endpoint."
    )
