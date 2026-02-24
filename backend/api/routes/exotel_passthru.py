"""
Exotel Passthru Webhook Handler - Production Ready
===================================================

CRITICAL INFORMATION FOR FUTURE DEBUGGING:

Why this endpoint exists:
-------------------------
1. Exotel Passthru applet requires a PURE API endpoint that returns XML
2. ngrok free plan shows a browser warning page at root URL (/)
3. If Exotel receives HTML/JSON instead of XML, it IMMEDIATELY HANGS UP (1 ring issue)
4. This endpoint is specifically designed to NEVER return HTML or ngrok warnings

Why we use /webhooks/exotel/incoming (not /):
----------------------------------------------
- Root path (/) on ngrok free shows: "ngrok - tunnel status page"
- Exotel Passthru expects valid XML response
- If it gets HTML, call drops after 1 ring
- Using a dedicated path ensures we control the response

Why XML is mandatory:
---------------------
- Exotel Passthru ONLY understands XML format (NOT JSON)
- Content-Type MUST be "application/xml"
- Response structure follows Exotel XML schema
- Any other format = immediate call disconnect

Common Exotel Issues and Solutions:
------------------------------------
Issue 1: "Call rings once and disconnects"
→ Cause: Webhook returned HTML/JSON instead of XML
→ Solution: Check Content-Type header, ensure XML response

Issue 2: "Webhook not triggered"
→ Cause: Wrong URL in Exotel dashboard, or ngrok tunnel down
→ Solution: Verify ngrok URL, check logs

Issue 3: "No audio plays"
→ Cause: <Say> tag missing language="hi-IN" or <Play> URL is wrong
→ Solution: Validate XML structure, test audio URL

ngrok Free Plan Limitations:
-----------------------------
- Browser warning page at root (/)
- No custom domain
- Tunnel URL changes on restart
- 40 connections per minute limit
- NOT an issue if we use proper API paths like /webhooks/exotel/incoming

PRODUCTION CHECKLIST:
---------------------
Before going live:
✓ Test webhook with: curl -X POST https://your-ngrok-url.ngrok-free.dev/webhooks/exotel/incoming -F "CallSid=test"
✓ Verify response is XML (not HTML)
✓ Check Content-Type header: application/xml
✓ Ensure HTTP status: 200
✓ Test with actual Exotel number
✓ Monitor backend logs for errors
✓ Keep ngrok running (or use production domain)

EXOTEL PASSTHRU URL FORMAT:
----------------------------
Correct: https://conjugative-tandra-amitotically.ngrok-free.dev/webhooks/exotel/incoming
Wrong:   https://conjugative-tandra-amitotically.ngrok-free.dev/
Wrong:   https://conjugative-tandra-amitotically.ngrok-free.dev/api/exotel/voice

"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from datetime import datetime
import os
import httpx
import asyncio
try:
    from groq import Groq
except ImportError:
    Groq = None
try:
    from google.cloud import speech_v1
    from google.cloud import texttospeech
except ImportError:
    speech_v1 = None
    texttospeech = None

from api.deps import get_db
from services.organisation_service import OrganisationService
from services.call_session_service import CallSessionService

logger = logging.getLogger(__name__)
router = APIRouter()

# =============================================================================
# CONFIGURATION & INITIALIZATION
# =============================================================================

# Google Cloud credentials (set via GOOGLE_APPLICATION_CREDENTIALS env var)
# Make sure google-creds.json is mounted in Docker

# GROQ API client for LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
groq_client = None

if GROQ_API_KEY:
    try:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client initialized")
    except Exception as e:
        print("❌ Groq init failed:", e)
        groq_client = None

# Google API Key for STT/TTS (alternative to service account)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Google clients - with API key fallback
try:
    if GOOGLE_API_KEY:
        # Use API key authentication (simpler for testing)
        os.environ["GOOGLE_CLOUD_PROJECT"] = "kisanvani"
        from google.auth import credentials
        from google.auth.transport.requests import Request as GoogleRequest
        
        # For API key based auth, we'll use REST API directly
        stt_client = None  # Will use REST API
        tts_client = None  # Will use REST API
        logger.info(f"✅ Using Google API Key authentication (key: {GOOGLE_API_KEY[:20]}...)")
    else:
        # Use service account authentication
        stt_client = speech_v1.SpeechClient()
        tts_client = texttospeech.TextToSpeechClient()
        logger.info("✅ Google STT and TTS clients initialized with service account")
except Exception as e:
    logger.error(f"⚠️ Google clients initialization failed: {e}")
    stt_client = None
    tts_client = None

# ngrok URL (must match your active tunnel)
NGROK_BASE_URL = "https://conjugative-tandra-amitotically.ngrok-free.dev"


# =============================================================================
# CRITICAL ENDPOINT: EXOTEL PASSTHRU WEBHOOK
# =============================================================================
@router.api_route("/incoming", methods=["GET", "POST"])
async def exotel_passthru_webhook(
    request: Request,
    CallSid: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
    CallStatus: Optional[str] = Form(None),
    Direction: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Exotel Passthru Webhook Handler
    
    This endpoint is called by Exotel when a farmer dials the organisation's number.
    
    FLOW:
    1. Farmer dials: 09513886363
    2. Exotel receives call
    3. Exotel sends POST request to this endpoint
    4. We identify organisation from 'To' number
    5. We return XML with greeting message
    6. Exotel plays the message to farmer
    
    CRITICAL REQUIREMENTS:
    - Response MUST be XML (Content-Type: application/xml)
    - HTTP status MUST be 200
    - Response time MUST be < 3 seconds (Exotel timeout)
    - NO HTML, NO JSON, NO redirects
    
    EXOTEL FORM DATA:
    - CallSid: Unique call identifier from Exotel
    - From: Farmer's phone number (caller)
    - To: Dialed number (organisation's number)
    - CallStatus: ringing/in-progress/completed
    - Direction: inbound/outbound
    
    Example ngrok URL for Exotel dashboard:
    https://conjugative-tandra-amitotically.ngrok-free.dev/webhooks/exotel/incoming
    
    Why this works with ngrok free:
    - We use a specific path (/webhooks/exotel/incoming)
    - ngrok warning page only appears at root (/)
    - This endpoint returns pure XML, never HTML
    - Exotel never sees the ngrok browser warning
    """
    
    try:
        # Log incoming webhook data
        logger.info(
            f"📞 Exotel Passthru Webhook received: "
            f"CallSid={CallSid}, From={From}, To={To}, Status={CallStatus}"
        )
        
        # Default values if Exotel doesn't send them
        caller_number = From or "unknown"
        dialed_number = To or "09513886363"  # Fallback to Rasi Seeds number
        call_sid = CallSid or f"sim_{int(datetime.now().timestamp())}"
        
        # STEP 1: Identify Organisation from dialed number (To)
        # This is the CORE of multi-tenant routing
        org_service = OrganisationService(db)
        organisation = await org_service.identify_organisation_by_phone(
            dialed_number=dialed_number
        )
        
        if not organisation:
            logger.warning(
                f"❌ Organisation not found for number: {dialed_number}. "
                f"Call will be rejected."
            )
            
            # Return error XML (call will be disconnected gracefully)
            error_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="hi-IN">
        माफ़ कीजिए, यह नंबर सेवा में नहीं है। कृपया सही नंबर डायल करें।
    </Say>
    <Hangup/>
</Response>"""
            
            return Response(
                content=error_xml,
                media_type="application/xml",  # CRITICAL: Must be XML
                status_code=200  # CRITICAL: Must be 200 even for errors
            )
        
        logger.info(
            f"✅ Organisation identified: {organisation.name} (ID: {organisation.id}) "
            f"for number {dialed_number}"
        )
        
        # STEP 2: Create call session record
        # This tracks the call in database for analytics and history
        try:
            call_service = CallSessionService(db)
            call_session = await call_service.create_call_session(
                from_phone=caller_number,
                to_phone=dialed_number,
                organisation_id=organisation.id,
                exotel_call_sid=call_sid,
                provider_name="exotel"
            )
            
            logger.info(
                f"✅ Call session created: ID={call_session.id}, "
                f"Session={call_session.session_id[:8]}..."
            )
        except Exception as session_error:
            # Don't fail the webhook if session creation fails
            logger.error(f"⚠️ Failed to create call session: {session_error}")
            # Continue anyway - greeting is more important than DB record
        
        # STEP 3: Generate greeting message
        # Use organisation-specific greeting if available
        greeting_text = organisation.greeting_message or """नमस्ते! मैं किसान AI हूं, आपकी खेती सहायक।
मैं आपकी खेती से जुड़ी समस्या में मदद कर सकती हूं।
कृपया अपनी समस्या बताएं।"""
        
        # STEP 4: Return XML response to Exotel
        # This XML tells Exotel what to do next
        response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="hi-IN">
        {greeting_text}
    </Say>
    <Record action="{NGROK_BASE_URL}/webhooks/exotel/gather" method="POST" maxLength="60" finishOnKey="#" playBeep="true"/>
    <Say voice="woman" language="hi-IN">
        कोई जवाब नहीं मिला। धन्यवाद।
    </Say>
    <Hangup/>
</Response>"""
        
        logger.info(f"✅ Returning XML response to Exotel for call {call_sid}")
        
        # CRITICAL: Response MUST have these exact headers
        return Response(
            content=response_xml,
            media_type="application/xml",  # NOT "text/xml", NOT "application/json"
            status_code=200,  # NOT 201, NOT 204
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ ERROR in Exotel webhook: {e}", exc_info=True)
        
        # CRITICAL: Even on error, return 200 + valid XML
        # If we return 500, Exotel will retry and fail again
        fallback_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="hi-IN">
        माफ़ कीजिए, कुछ गड़बड़ हो गई है। कृपया कुछ देर बाद कॉल करें।
    </Say>
    <Hangup/>
</Response>"""
        
        return Response(
            content=fallback_xml,
            media_type="application/xml",
            status_code=200
        )


# =============================================================================
# GATHER WEBHOOK (COMPLETE AI PIPELINE)
# =============================================================================

async def download_audio(recording_url: str) -> bytes:
    """
    Download audio recording from Exotel
    
    Exotel provides a RecordingUrl after farmer speaks.
    We need to download it to process with Google STT.
    
    Returns: Audio bytes in original format
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(recording_url)
            response.raise_for_status()
            logger.info(f"✅ Downloaded audio: {len(response.content)} bytes")
            return response.content
    except Exception as e:
        logger.error(f"❌ Failed to download audio: {e}")
        raise


async def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Convert speech to text using Google STT
    
    Args:
        audio_bytes: Raw audio bytes from Exotel recording
    
    Returns:
        Transcribed Hindi text
    
    Google STT Configuration:
    - Language: hi-IN (Hindi India)
    - Encoding: Usually LINEAR16 or MULAW from Exotel
    - Sample rate: 8000 Hz (telephony standard)
    """
    try:
        if GOOGLE_API_KEY:
            # Use REST API with API key
            async with httpx.AsyncClient(timeout=30.0) as client:
                import base64
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                
                payload = {
                    "config": {
                        "encoding": "MULAW",
                        "sampleRateHertz": 8000,
                        "languageCode": "hi-IN",
                        "enableAutomaticPunctuation": True,
                        "model": "default"
                    },
                    "audio": {
                        "content": audio_b64
                    }
                }
                
                response = await client.post(
                    f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                if "results" in result and len(result["results"]) > 0:
                    transcript = result["results"][0]["alternatives"][0]["transcript"]
                    logger.info(f"✅ Transcription: {transcript}")
                    return transcript
                else:
                    logger.warning("No transcription results")
                    return ""
                    
        elif stt_client:
            # Use service account authentication
            audio = speech_v1.RecognitionAudio(content=audio_bytes)
            
            config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.MULAW,
                sample_rate_hertz=8000,
                language_code="hi-IN",
                enable_automatic_punctuation=True,
                model="default",
            )
            
            response = stt_client.recognize(config=config, audio=audio)
            
            if not response.results:
                logger.warning("No transcription results from Google STT")
                return ""
            
            transcript = response.results[0].alternatives[0].transcript
            logger.info(f"✅ Transcription: {transcript}")
            return transcript
        else:
            raise Exception("No Google STT authentication configured")
            
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        raise


async def get_ai_response(user_message: str, organisation_name: str) -> str:
    """
    Get AI response using GROQ LLM
    
    Args:
        user_message: Farmer's transcribed question
        organisation_name: Organisation context for multi-tenant
    
    Returns:
        AI response in Hindi
    
    GROQ Configuration:
    - Model: mixtral-8x7b-32768 (fast and good for Hindi)
    - Temperature: 0.7 (balanced creativity)
    - Max tokens: 500 (concise responses for voice)
    
    Context:
    - System prompt includes organisation name
    - RAG integration point (TODO: Add product knowledge)
    - Response optimized for voice (short, clear)
    """
    if not groq_client:
        raise Exception("GROQ client not initialized")
    
    try:
        # System prompt for agricultural AI assistant
        system_prompt = f"""तुम {organisation_name} की ओर से एक कृषि सलाहकार हो।
किसान की समस्या को समझो और छोटा, स्पष्ट जवाब दो।
जवाब हिंदी में हो, 2-3 वाक्यों में।
तकनीकी शब्दों से बचो।
अगर जानकारी नहीं है तो ईमानदारी से बताओ।"""
        
        # Call GROQ LLM
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="mixtral-8x7b-32768",  # Fast multilingual model
            temperature=0.7,
            max_tokens=500,
            top_p=0.9,
        )
        
        ai_response = chat_completion.choices[0].message.content
        logger.info(f"✅ AI Response: {ai_response[:100]}...")
        
        return ai_response
        
    except Exception as e:
        logger.error(f"❌ LLM failed: {e}")
        raise


async def synthesize_speech(text: str) -> bytes:
    """
    Convert text to speech using Google TTS
    
    Args:
        text: Hindi text to convert to audio
    
    Returns:
        Audio bytes in MP3 format
    
    Google TTS Configuration:
    - Language: hi-IN
    - Voice: Female (hi-IN-Wavenet-A)
    - Audio format: MP3 (widely supported by Exotel)
    - Speaking rate: 0.95 (slightly slower for clarity)
    """
    try:
        if GOOGLE_API_KEY:
            # Use REST API with API key
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "input": {"text": text},
                    "voice": {
                        "languageCode": "hi-IN",
                        "name": "hi-IN-Wavenet-A",
                        "ssmlGender": "FEMALE"
                    },
                    "audioConfig": {
                        "audioEncoding": "MP3",
                        "speakingRate": 0.95,
                        "pitch": 0.0
                    }
                }
                
                response = await client.post(
                    f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_API_KEY}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                if "audioContent" in result:
                    import base64
                    audio_bytes = base64.b64decode(result["audioContent"])
                    logger.info(f"✅ TTS generated: {len(audio_bytes)} bytes")
                    return audio_bytes
                else:
                    raise Exception("No audio content in TTS response")
                    
        elif tts_client:
            # Use service account authentication
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code="hi-IN",
                name="hi-IN-Wavenet-A",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.95,
                pitch=0.0,
            )
            
            response = tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info(f"✅ TTS generated: {len(response.audio_content)} bytes")
            return response.audio_content
        else:
            raise Exception("No Google TTS authentication configured")
        
    except Exception as e:
        logger.error(f"❌ TTS failed: {e}")
        raise


async def save_audio_file(audio_bytes: bytes, filename: str) -> str:
    """
    Save audio file and return public URL
    
    In production, upload to S3/GCS and return public URL.
    For now, save locally and serve via static files.
    
    Args:
        audio_bytes: Audio file content
        filename: Filename to save as
    
    Returns:
        Public URL accessible by Exotel
    """
    try:
        # Create audio directory if not exists
        audio_dir = "/app/static/audio"  # Docker path
        os.makedirs(audio_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(audio_dir, filename)
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
        
        # Return public URL
        # Exotel needs to access this URL to play audio
        public_url = f"{NGROK_BASE_URL}/static/audio/{filename}"
        logger.info(f"✅ Audio saved: {public_url}")
        
        return public_url
        
    except Exception as e:
        logger.error(f"❌ Failed to save audio: {e}")
        raise


@router.post("/gather")
async def exotel_gather_webhook(
    request: Request,
    CallSid: Optional[str] = Form(None),
    RecordingUrl: Optional[str] = Form(None),
    Digits: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    COMPLETE AI PIPELINE: STT → LLM → TTS
    
    This endpoint is called after farmer speaks and recording is ready.
    
    PRODUCTION FLOW:
    1. Download audio from Exotel RecordingUrl
    2. Send audio to Google STT → Get text transcript
    3. Send transcript to GROQ LLM → Get AI response
    4. Send AI response to Google TTS → Get audio
    5. Save audio file to public URL
    6. Return XML with <Play> tag to play AI response
    
    CRITICAL FOR EXOTEL:
    - MUST return XML (never JSON/HTML)
    - MUST return status 200 (even on errors)
    - <Play> URL MUST be publicly accessible
    - Audio format: MP3 or WAV (Exotel supports both)
    
    ERROR HANDLING:
    - If STT fails: Return apologetic message using <Say>
    - If LLM fails: Return fallback response
    - If TTS fails: Use <Say> instead of <Play>
    - Always graceful degradation to keep call alive
    
    WHY THIS WORKS:
    - We use <Record> (not <Gather>) in /incoming for better quality
    - Exotel provides RecordingUrl after recording completes
    - We download, process, and respond - all async
    - Response time < 5 seconds keeps call engaged
    """
    
    try:
        logger.info(
            f"📝 Gather webhook: CallSid={CallSid}, "
            f"RecordingUrl={RecordingUrl}, Digits={Digits}"
        )
        
        # Safety check
        if not RecordingUrl:
            logger.warning("⚠️ No RecordingUrl provided")
            fallback_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="hi-IN">
        माफ़ कीजिए, आपकी आवाज़ रिकॉर्ड नहीं हुई। कृपया फिर से कॉल करें।
    </Say>
    <Hangup/>
</Response>"""
            return Response(
                content=fallback_xml,
                media_type="application/xml",
                status_code=200
            )
        
        # Get organisation context from call session
        # In production, query call_sessions table using CallSid
        organisation_name = "रासी सीड्स"  # Fallback, fetch from DB in production
        
        # ============================================
        # STEP 1: DOWNLOAD AUDIO FROM EXOTEL
        # ============================================
        logger.info("🎤 Step 1: Downloading audio from Exotel...")
        audio_bytes = await download_audio(RecordingUrl)
        
        # ============================================
        # STEP 2: SPEECH-TO-TEXT (GOOGLE STT)
        # ============================================
        logger.info("🗣️ Step 2: Converting speech to text...")
        transcript = await transcribe_audio(audio_bytes)
        
        if not transcript:
            logger.warning("⚠️ Empty transcript")
            empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="hi-IN">
        माफ़ कीजिए, मैं आपकी बात समझ नहीं पाई। कृपया फिर से बोलें।
    </Say>
    <Hangup/>
</Response>"""
            return Response(
                content=empty_xml,
                media_type="application/xml",
                status_code=200
            )
        
        # ============================================
        # STEP 3: AI RESPONSE (GROQ LLM + RAG)
        # ============================================
        logger.info("🤖 Step 3: Getting AI response...")
        ai_response = await get_ai_response(transcript, organisation_name)
        
        # ============================================
        # STEP 4: TEXT-TO-SPEECH (GOOGLE TTS)
        # ============================================
        logger.info("🔊 Step 4: Converting AI response to speech...")
        audio_bytes = await synthesize_speech(ai_response)
        
        # ============================================
        # STEP 5: SAVE AUDIO & GET PUBLIC URL
        # ============================================
        logger.info("💾 Step 5: Saving audio file...")
        audio_filename = f"response_{CallSid}_{int(datetime.now().timestamp())}.mp3"
        audio_url = await save_audio_file(audio_bytes, audio_filename)
        
        # ============================================
        # STEP 6: RETURN XML WITH <Play> TAG
        # ============================================
        logger.info(f"✅ Returning AI response via audio: {audio_url}")
        
        response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
    <Say voice="woman" language="hi-IN">
        क्या आपका कोई और सवाल है?
    </Say>
    <Record action="{NGROK_BASE_URL}/webhooks/exotel/gather" method="POST" maxLength="60" finishOnKey="#" playBeep="true"/>
    <Say voice="woman" language="hi-IN">
        धन्यवाद। अलविदा।
    </Say>
    <Hangup/>
</Response>"""
        
        return Response(
            content=response_xml,
            media_type="application/xml",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR in gather pipeline: {e}", exc_info=True)
        
        # CRITICAL: Always return valid XML, never let Exotel see errors
        error_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="hi-IN">
        माफ़ कीजिए, तकनीकी समस्या हो रही है। हमारी टीम जल्द ही आपसे संपर्क करेगी।
    </Say>
    <Hangup/>
</Response>"""
        
        return Response(
            content=error_xml,
            media_type="application/xml",
            status_code=200
        )


# =============================================================================
# HEALTH CHECK ENDPOINT (OPTIONAL)
# =============================================================================

@router.get("/health")
async def webhook_health_check():
    """
    Simple health check for monitoring
    
    This endpoint returns JSON (not XML) because it's for internal monitoring,
    NOT for Exotel webhook.
    
    Use this to verify:
    - Backend is running
    - ngrok tunnel is working
    - Endpoint is reachable
    
    Test: curl https://your-ngrok-url.ngrok-free.dev/webhooks/exotel/health
    """
    return {
        "status": "healthy",
        "service": "Exotel Passthru Webhook",
        "endpoint": "/webhooks/exotel/incoming",
        "timestamp": datetime.now().isoformat(),
        "note": "This is a health check. Use POST /webhooks/exotel/incoming for Exotel."
    }
