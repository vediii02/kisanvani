"""
Exotel Webhook Routes
Handle Exotel callbacks for calls
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from api.deps import get_db
from services.exotel_service import exotel_service
from services.stt_service import stt_service
from services.intent_service import intent_service
from services.rag_response_service import rag_service
from services.dialogue_manager import dialogue_manager
from db.models.call_session import CallSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/voice")
async def exotel_voice_webhook(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming call voice webhook from Exotel
    Returns XML response for call flow
    """
    try:
        call_data = {
            "CallSid": CallSid,
            "From": From,
            "To": To
        }
        
        logger.info(f"Voice webhook: {call_data}")
        
        # Generate initial response
        xml = await exotel_service.handle_incoming_call(call_data)
        
        return Response(content=xml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Voice webhook error: {e}", exc_info=True)
        error_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="hi-IN">
        माफ़ कीजिए, कुछ गड़बड़ हो गई है। कृपया बाद में कॉल करें।
    </Say>
    <Hangup/>
</Response>"""
        return Response(content=error_xml, media_type="application/xml")


@router.post("/gather")
async def exotel_gather_webhook(
    request: Request,
    CallSid: str = Form(...),
    RecordingUrl: Optional[str] = Form(None),
    Digits: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle gathered input (speech or DTMF) from Exotel
    """
    try:
        gather_data = {
            "CallSid": CallSid,
            "RecordingUrl": RecordingUrl,
            "Digits": Digits
        }
        
        logger.info(f"Gather webhook: {gather_data}")
        
        # Process the input
        xml = await exotel_service.handle_gather(gather_data)
        
        return Response(content=xml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Gather webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/status")
async def exotel_status_webhook(
    request: Request,
    CallSid: str = Form(...),
    Status: str = Form(...),
    Duration: Optional[int] = Form(0),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle call status updates from Exotel
    """
    try:
        status_data = {
            "CallSid": CallSid,
            "Status": Status,
            "Duration": Duration
        }
        
        logger.info(f"Status webhook: {status_data}")
        
        # Process status update
        result = await exotel_service.handle_status_callback(status_data)
        
        # Update call session in database
        # TODO: Find call by call_sid and update
        
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"Status webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recording")
async def exotel_recording_webhook(
    request: Request,
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle recording ready callback from Exotel
    """
    try:
        logger.info(f"Recording ready: {CallSid} - {RecordingUrl}")
        
        # TODO: Download and process recording
        # 1. Download audio from RecordingUrl
        # 2. Transcribe using STT service
        # 3. Detect intent
        # 4. Generate AI response
        # 5. Update call session
        
        return {"success": True, "message": "Recording received"}
        
    except Exception as e:
        logger.error(f"Recording webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/make-call")
async def make_outbound_call(
    from_number: str,
    to_number: str,
    call_session_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Make outbound call via Exotel
    """
    try:
        custom_field = str(call_session_id) if call_session_id else None
        
        result = await exotel_service.make_call(
            from_number=from_number,
            to_number=to_number,
            custom_field=custom_field
        )
        
        if result["success"] and call_session_id:
            # Update call session with Exotel SID
            call_session = await db.get(CallSession, call_session_id)
            if call_session:
                call_session.exotel_sid = result["call_sid"]
                await db.commit()
        
        return result
        
    except Exception as e:
        logger.error(f"Make call error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
