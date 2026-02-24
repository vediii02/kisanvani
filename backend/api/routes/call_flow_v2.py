"""
Enhanced Call Flow API - REAL CALL READY
Greeting + Real Exotel Call + RAG + Product Suggestion
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import os

from api.deps import get_db
from services.organisation_service import OrganisationService
from services.call_session_service import CallSessionService
from services.welcome_service import WelcomeService
from services.farmer_query_service import FarmerQueryService

# AI PIPELINE
from services.stt_service import stt_service
from services.tts_service import TTSService
from services.dialogue_manager import dialogue_manager, DialogueState
from services.rag_advisor import generate_answer
from services.product_advisor import generate_final_answer

from core.llm import llm
from core.call_provider_factory import get_call_provider

logger = logging.getLogger(__name__)
router = APIRouter()
tts_service = TTSService()

# =====================================================
# 1️⃣ INCOMING CALL → GREETING
# =====================================================

@router.post("/incoming")
async def handle_incoming_call(request: Request, db: AsyncSession = Depends(get_db)):
    provider = get_call_provider()
    call_data = provider.parse_incoming_call(await request.json())

    org_service = OrganisationService(db)
    organisation = await org_service.identify_organisation_by_phone(
        call_data["to_phone"]
    )

    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    call_service = CallSessionService(db)
    call_session = await call_service.create_call_session(
        from_phone=call_data["from_phone"],
        to_phone=call_data["to_phone"],
        organisation_id=organisation.id,
        exotel_call_sid=call_data["provider_call_id"],
        provider_name=call_data["provider_name"]
    )

    await call_service.initialize_call_state(
        call_session_id=call_session.id,
        organisation_id=organisation.id
    )

    welcome_service = WelcomeService()
    audio_bytes, filename = await welcome_service.create_welcome_audio(
        org_name=organisation.name,
        session_id=call_session.id
    )

    return {
        "success": True,
        "call_session_id": call_session.id,
        "audio_url": f"/api/call-flow/audio/{filename}"
    }

# =====================================================
# 2️⃣ REAL EXOTEL AUDIO CALLBACK (🔥 MAIN BRAIN 🔥)
# =====================================================

@router.post("/exotel/passthru")
async def exotel_passthru(request: Request, db: AsyncSession = Depends(get_db)):
    """
    REAL farmer speech comes here from Exotel
    """
    form = await request.form()

    audio_url = form.get("RecordingUrl")
    call_sid = form.get("CallSid")

    if not audio_url or not call_sid:
        return PlainTextResponse("OK")

    # 🔹 Download audio
    import httpx
    async with httpx.AsyncClient() as client:
        audio_resp = await client.get(audio_url)
        audio_bytes = audio_resp.content

    # 🔹 STT
    stt_result = await stt_service.transcribe_audio(
        audio_data=audio_bytes,
        language="hi-IN"
    )

    if not stt_result["success"]:
        return PlainTextResponse("OK")

    user_query = stt_result["text"]
    logger.info(f"🎤 Farmer said: {user_query}")

    # 🔹 Get call session
    call_service = CallSessionService(db)
    call_session = await call_service.get_by_provider_sid(call_sid)

    if not call_session:
        return PlainTextResponse("OK")

    # 🔹 Dialogue context
    dialogue_context = dialogue_manager.initialize_dialogue(call_session.id)

    # (Temporary intent – next step me auto hoga)
    intent = "nutrient_problem"
    entities = {}

    # 🔥 AGRI + PRODUCT AI
    agri_answer = generate_answer(user_query, llm)
    final_answer = generate_final_answer(
        user_query=user_query,
        agri_answer=agri_answer,
        llm=llm
    )

    # 🔹 Dialogue update
    await dialogue_manager.update_dialogue_state(
        dialogue_context=dialogue_context,
        user_input=user_query,
        intent=intent,
        entities=entities,
        ai_response=final_answer,
        db=db
    )

    # 🔹 Save farmer query and answer
    farmer_query_service = FarmerQueryService(db)
    await farmer_query_service.save_query(
        call_session_id=call_session.id,
        farmer_id=call_session.farmer_id,
        organisation_id=call_session.organisation_id if hasattr(call_session, 'organisation_id') else None,
        question=user_query,
        answer=final_answer,
        intent=intent
    )

    # 🔹 TTS
    tts_result = await tts_service.synthesize_speech(
        text=final_answer,
        language="hi",
        session_id=str(call_session.id)
    )

    # 🔹 Tell Exotel to play audio
    response_xml = f"""
    <Response>
        <Play>{tts_result["audio_url"]}</Play>
    </Response>
    """

    return PlainTextResponse(response_xml, media_type="application/xml")

# =====================================================
# 3️⃣ AUDIO SERVING
# =====================================================

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    audio_dir = "static/audio"
    path = os.path.join(audio_dir, filename)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio not found")

    return FileResponse(path, media_type="audio/mpeg")
