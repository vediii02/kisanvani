"""
Exotel Live Calling System - Production Implementation
=======================================================

Handles Exotel Passthru webhook integration for live voice calls.

Endpoints:
- POST /api/exotel/inbound  - Incoming call handler
- POST /api/exotel/recording - Recording processor

Domain: https://kisan.rechargestudio.com
"""

from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
import httpx

from api.deps import get_db
from services.organisation_service import OrganisationService
from services.call_session_service import CallSessionService
from services.conversation_manager import conversation_manager
from services.stt_service import STTService
from services.tts_service import TTSService

logger = logging.getLogger(__name__)
router = APIRouter()

# Audio URLs
BASE_URL = "https://kisan.rechargestudio.com"
GREETING_AUDIO = f"{BASE_URL}/audio/greeting_hi.mp3"
RECORDING_ENDPOINT = f"{BASE_URL}/api/exotel/recording"
ERROR_AUDIO = f"{BASE_URL}/audio/error_hi.mp3"

# Services
stt_service = STTService()
tts_service = TTSService()


# ============================================================================
# XML HELPER FUNCTIONS
# ============================================================================

def create_greeting_xml() -> str:
    """
    Generate XML for initial greeting and recording
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{GREETING_AUDIO}</Play>
    <Record action="{RECORDING_ENDPOINT}" method="POST" maxLength="60" playBeep="true" />
</Response>"""


def create_response_xml(audio_url: str) -> str:
    """
    Generate XML for AI response playback and next recording
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
    <Record action="{RECORDING_ENDPOINT}" method="POST" maxLength="60" playBeep="true" />
</Response>"""


def create_error_xml() -> str:
    """
    Generate XML for error handling
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{ERROR_AUDIO}</Play>
    <Hangup />
</Response>"""


# ============================================================================
# HELPER FUNCTION: PROCESS CALL AUDIO (INTEGRATES WITH EXISTING SERVICES)
# ============================================================================

async def process_call_audio(
    recording_url: str,
    call_sid: str,
    from_number: str,
    to_number: str,
    db: AsyncSession
) -> str:
    """
    Process farmer's audio recording and generate AI response
    
    This function integrates with existing services:
    1. Download audio from Exotel
    2. Transcribe using STT
    3. Process with AI conversation manager
    4. Generate audio response using TTS
    5. Return public audio URL
    
    Args:
        recording_url: Exotel's recording URL
        call_sid: Exotel call ID
        from_number: Farmer's phone number
        to_number: Organisation's phone number
        db: Database session
    
    Returns:
        Public audio URL for AI response
    """
    try:
        # Step 1: Download audio from Exotel
        logger.info(f"📥 Downloading recording from: {recording_url}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            audio_response = await client.get(recording_url)
            audio_response.raise_for_status()
            audio_bytes = audio_response.content
        
        logger.info(f"✅ Downloaded {len(audio_bytes)} bytes")
        
        # Step 2: Find or create call session
        org_service = OrganisationService(db)
        organisation = await org_service.identify_organisation_by_phone(to_number)
        
        if not organisation:
            logger.error(f"❌ Organisation not found for phone: {to_number}")
            return ERROR_AUDIO
        
        # Get or create call session
        call_service = CallSessionService(db)
        call_session = await call_service.get_or_create_session_by_exotel_sid(
            exotel_call_sid=call_sid,
            from_phone=from_number,
            to_phone=to_number,
            organisation_id=organisation.id
        )
        
        logger.info(f"📞 Call session ID: {call_session.id}")
        
        # Step 3: Transcribe audio (STT)
        logger.info("🎤 Transcribing audio...")
        stt_result = await stt_service.transcribe_audio(
            audio_data=audio_bytes,
            language="hi"
        )
        
        if not stt_result.get("success"):
            logger.error(f"❌ STT failed: {stt_result.get('error')}")
            return ERROR_AUDIO
        
        transcribed_text = stt_result.get("text", "")
        logger.info(f"📝 Transcribed: {transcribed_text}")
        
        if not transcribed_text.strip():
            logger.warning("⚠️ Empty transcription")
            return ERROR_AUDIO
        
        # Step 4: Process with AI conversation manager
        logger.info("🤖 Processing with AI...")
        ai_result = await conversation_manager.process_message(
            db=db,
            call_session_id=call_session.id,
            farmer_message=transcribed_text
        )
        
        if not ai_result.get("success"):
            logger.error(f"❌ AI processing failed: {ai_result.get('error')}")
            return ERROR_AUDIO
        
        ai_response_text = ai_result.get("message", "")
        logger.info(f"💬 AI Response: {ai_response_text}")
        
        # Step 5: Generate audio response (TTS)
        logger.info("🔊 Generating audio response...")
        tts_result = await tts_service.synthesize_speech(
            text=ai_response_text,
            language="hi",
            session_id=f"{call_session.id}_{call_sid}"
        )
        
        if not tts_result.get("success"):
            logger.error(f"❌ TTS failed: {tts_result.get('error')}")
            return ERROR_AUDIO
        
        audio_url = tts_result.get("audio_url", "")
        logger.info(f"✅ Generated audio: {audio_url}")
        
        return audio_url
        
    except Exception as e:
        logger.error(f"❌ Error processing call audio: {e}", exc_info=True)
        return ERROR_AUDIO


# ============================================================================
# ENDPOINT 1: INBOUND CALL HANDLER
# ============================================================================

@router.post("/inbound")
async def handle_inbound_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming call from Exotel Passthru
    
    Exotel sends:
    - CallSid: Unique call identifier
    - From: Farmer's phone number
    - To: Organisation's phone number
    - CallStatus: Call status (ringing, in-progress, etc.)
    
    Returns:
    - XML response with greeting audio and recording instruction
    """
    try:
        logger.info(
            f"📞 Inbound call: CallSid={CallSid}, "
            f"From={From}, To={To}, Status={CallStatus}"
        )
        
        # Validate organisation exists
        org_service = OrganisationService(db)
        organisation = await org_service.identify_organisation_by_phone(To)
        
        if not organisation:
            logger.error(f"❌ Organisation not found for phone: {To}")
            xml = create_error_xml()
            return Response(content=xml, media_type="application/xml")
        
        logger.info(f"✅ Organisation found: {organisation.name}")
        
        # Create call session
        call_service = CallSessionService(db)
        call_session = await call_service.create_call_session(
            from_phone=From,
            to_phone=To,
            organisation_id=organisation.id,
            exotel_call_sid=CallSid,
            provider_name="exotel"
        )
        
        logger.info(f"✅ Call session created: ID={call_session.id}")
        
        # Return greeting XML
        xml = create_greeting_xml()
        return Response(content=xml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"❌ Error handling inbound call: {e}", exc_info=True)
        xml = create_error_xml()
        return Response(content=xml, media_type="application/xml")


# ============================================================================
# ENDPOINT 2: RECORDING HANDLER
# ============================================================================

@router.post("/recording")
async def handle_recording(
    RecordingUrl: str = Form(...),
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    RecordingDuration: Optional[str] = Form(None),
    RecordingSize: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle recording callback from Exotel
    
    Exotel sends:
    - RecordingUrl: URL to download the recording
    - CallSid: Unique call identifier
    - From: Farmer's phone number
    - To: Organisation's phone number
    - RecordingDuration: Length of recording in seconds
    - RecordingSize: Size of recording in bytes
    
    Returns:
    - XML response with AI audio and next recording instruction
    """
    try:
        logger.info(
            f"🎙️ Recording received: CallSid={CallSid}, "
            f"URL={RecordingUrl}, Duration={RecordingDuration}s"
        )

        # STEP 1: Use provider-agnostic adapter to parse status callback
        from core.call_provider_factory import get_call_provider
        provider_adapter = get_call_provider()
        callback_payload = {
            'CallSid': CallSid,
            'From': From,
            'To': To,
            'Status': 'completed',  # Exotel always sends completed for recording
            'EndTime': None,
            'Duration': RecordingDuration
        }
        call_data = provider_adapter.parse_status_callback(callback_payload)

        # STEP 2: Update call session status
        from services.call_session_service import CallSessionService
        call_service = CallSessionService(db)
        # Find session by provider_call_id
        result = await db.execute(
            select(CallSession).where(CallSession.provider_call_id == call_data['provider_call_id'])
        )
        call_session = result.scalars().first()
        if call_session:
            await call_service.update_call_status(
                call_session_id=call_session.id,
                status=CallStatus.COMPLETED,
                end_time=datetime.utcnow()
            )
        else:
            logger.warning(f"No call session found for provider_call_id={call_data['provider_call_id']}")

        # Process recording through existing services
        audio_url = await process_call_audio(
            recording_url=RecordingUrl,
            call_sid=CallSid,
            from_number=From,
            to_number=To,
            db=db
        )

        # Generate response XML
        if audio_url and audio_url != ERROR_AUDIO:
            logger.info(f"✅ Returning AI response: {audio_url}")
            xml = create_response_xml(audio_url)
        else:
            logger.error("❌ Failed to generate AI response")
            xml = create_error_xml()

        return Response(content=xml, media_type="application/xml")

    except Exception as e:
        logger.error(f"❌ Error handling recording: {e}", exc_info=True)
        xml = create_error_xml()
        return Response(content=xml, media_type="application/xml")
