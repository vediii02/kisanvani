# ============================================================
# FREE-FORM FARMING QUESTION HANDLER (AFTER PROFILE)
# ============================================================

from fastapi import APIRouter, Response, Request, status, Depends
import json
import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .session_manager import SessionManager
from db.session import get_db
from db.models.call_session import CallSession
from db.models.call_transcript import CallTranscript, Speaker
from db.models.farmer import Farmer
from db.models.case import Case
from db.models.advisory import Advisory
from services.farmer_query_service import FarmerQueryService
from services.product_advisor import generate_final_answer
from core.llm import llm
from rag.rag_service import get_rag_advisory
from rag_pipeline.RAG_BOT.rag_service import run_rag_chat
from db.models.farmer_questions import FarmerQuestion
from db.models.company import Company
from sqlalchemy import select, delete
import logging
logger = logging.getLogger(__name__)



router = APIRouter()
session_manager = SessionManager()
FLOW_PATH = "/app/conversation/farmer_flow.json"
NGROK_ACTION = "https://conjugative-tandra-amitotically.ngrok-free.dev/api/twilio/next-step"
NGROK_ACTIONN =  "https://conjugative-tandra-amitotically.ngrok-free.dev/api/twilio/free-question"
NGROK_RAG_RESPONSE = "https://conjugative-tandra-amitotically.ngrok-free.dev/generate-response"
NGROK_CONFIRM_ADVISORY = "https://conjugative-tandra-amitotically.ngrok-free.dev/api/twilio/confirm-advisory"
# ============================================================
# UTILS
# ============================================================

def clean_speech(text: str) -> str:
    """Clean and normalize speech input"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove special characters if needed
    text = re.sub(r'[^\w\s\u0900-\u097F]', '', text)
    return text.strip()


def validate_answer(field: str, answer: str) -> bool:
    """Validate farmer's answer based on field type"""
    if not answer or not answer.strip():
        return False
    
    answer = answer.strip()
    
    # Field-specific validation
    if field == "land_size":
        # Check if it contains numbers
        return bool(re.search(r'\d+', answer))
    elif field == "crop_area":
        return bool(re.search(r'\d+', answer))
    elif field in ["name", "village", "district", "state", "crop_type", "problem_area"]:
        # Text fields should have at least 2 characters
        return len(answer) >= 2
    
    return True


def repeat_question(question: str, message: str) -> Response:
    """Helper to repeat a question with an error message"""
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">{message}</Say>
    <Gather input="speech"
            action="{NGROK_ACTION}"
            method="POST"
            timeout="20"
            speechTimeout="auto"
            actionOnEmptyResult="true"
            language="hi-IN">
        <Say language="hi-IN">{question}</Say>
    </Gather>
</Response>
'''
    return Response(content=twiml, media_type="text/xml; charset=utf-8")

async def delete_incomplete_farmer(db: AsyncSession, call_sid: str):
    """
    Delete incomplete farmer record and associated call session/transcripts.
    Called when user doesn't respond and call is terminated.
    
    Args:
        db: Database session
        call_sid: Twilio CallSid
    """
    # Get the call session
    result = await db.execute(
        select(CallSession).where(CallSession.session_id == call_sid)
    )
    call_session = result.scalars().first()
    
    if not call_session:
        return
    
    farmer_id = call_session.farmer_id
    
    # ORDER MATTERS - Delete in reverse dependency order:
    
    # 1. Delete all transcripts first (child of call_session)
    if call_session.id:
        await db.execute(
            delete(CallTranscript).where(CallTranscript.call_session_id == call_session.id)
        )
    
    # 2. Delete the call session (child of farmer)
    await db.execute(
        delete(CallSession).where(CallSession.session_id == call_sid)
    )
    
    # 3. Finally delete the farmer (parent)
    if farmer_id:
        await db.execute(
            delete(Farmer).where(Farmer.id == farmer_id)
        )
    
    await db.commit()


# ============================================================
# FREE-FORM FARMING QUESTION HANDLER (AFTER PROFILE)
# ============================================================

@router.api_route(
    "/twilio/free-question",
    methods=["POST"],
    response_model=None,
    include_in_schema=True,
    tags=["Twilio"]
)
@router.api_route(
    "/api/twilio/free-question",
    methods=["POST"],
    response_model=None,
    include_in_schema=True,
    tags=["Twilio"]
)
async def twilio_free_question(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    call_sid = form.get("CallSid")
    farmer_input = form.get("SpeechResult")
    phone_number = form.get("From")

    # return call_sid, farmer_input,phone_number

    # Edge case: silence, noise, or empty input
    if not call_sid or not farmer_input or not farmer_input.strip():
        return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">आपकी आवाज़ स्पष्ट नहीं थी। कृपया फिर से बोलें।</Say>
    <Gather input="speech"
            action="/api/twilio/free-question"
            method="POST"
            timeout="20"
            speechTimeout="auto"
            language="hi-IN">
        <Say language="hi-IN">कृपया अपना जवाब या सवाल बोलें।</Say>
    </Gather>
</Response>
''', media_type="text/xml; charset=utf-8")
    
  # ============================================================
    # LOOKUP EXISTING FARMER AND USE THEIR OLD SESSION
    # ============================================================
    
    # First, find the farmer by phone number
    farmer_result = await db.execute(
        select(Farmer)
        .where(Farmer.phone_number == phone_number)
        .order_by(Farmer.id.desc())
        .limit(1)
    )
    farmer = farmer_result.scalars().first()
    
    call_session = None
    
    if farmer:
        # Farmer exists - get their most recent CallSession
        session_result = await db.execute(
            select(CallSession)
            .where(CallSession.farmer_id == farmer.id)
            .order_by(CallSession.id.desc())
            .limit(1)
        )
        call_session = session_result.scalars().first()
        
        logger.info(f"Existing farmer found: {farmer.id}, Using old session: {call_session.session_id if call_session else 'None'}")
    
    # Get or create call session
    # session_result = await db.execute(select(CallSession).where(CallSession.session_id == call_sid))
    # call_session = session_result.scalars().first()
    
    company = await db.execute(select(Company).where(Company.phone == phone_number))
    company = company.scalars().first()

    if not call_session:
        call_session = CallSession(
            session_id=call_sid,
            phone_number=phone_number,
            provider_call_id=call_sid
        )
        db.add(call_session)
        await db.commit()
        await db.refresh(call_session)


        if farmer:
            call_session.farmer_id = farmer.id
            await db.commit()
	    
	    # Get company information
    company = await db.execute(select(Company).where(Company.phone == phone_number))
    company = company.scalars().first()

    # If we still don't have a farmer (shouldn't happen in normal flow), look them up
    if not farmer:
        if call_session.farmer_id:
            farmer_result = await db.execute(select(Farmer).where(Farmer.id == call_session.farmer_id))
            farmer = farmer_result.scalars().first()
        else:
            farmer_result = await db.execute(
                select(Farmer).where(Farmer.phone_number == phone_number).order_by(Farmer.id.desc())
            )
            farmer = farmer_result.scalars().first()

   
    try:

        # company_id="_abc_company"
        # company_name="ABC agro"
        # session_id="session_1"

        company_id=str(company.id)
        company_name=company.name
        session_id=call_sid
        
        rag_text = run_rag_chat(farmer_input,company_id,company_name,session_id)
        # rag_text = rag_text or ""
        # rag_text="rag text generated"

        call_session.advisory_generated = True
        call_session.advisory_text = rag_text
        await db.commit() 
        await db.refresh(call_session)
    

    except Exception as e:
        rag_text = "माफ़ कीजिए, अभी तकनीकी समस्या है। कृपया बाद में प्रयास करें।"
    

    if rag_text == "आपकी सहायता के लिए हमारे कृषि सहायक जल्द ही आपको कॉल करेंगे। आपके समय और विश्वास के लिए धन्यवाद।":
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say language="hi-IN">"आपकी सहायता के लिए हमारे कृषि सहायक जल्द ही आपको कॉल करेंगे। आपके समय और विश्वास के लिए धन्यवाद।"</Say>
            <Pause length="1"/>
        </Response>
        '''
        return Response(content=twiml, media_type="text/xml; charset=utf-8")
    
#     # Save Q&A to farmer_queries
    farmer_query_service = FarmerQueryService(db)
    await farmer_query_service.save_query(
        call_session_id=call_session.session_id,
        farmer_id=farmer.id,
        answer=rag_text,
        company_id = company.id,
        organisation_id=company.organisation_id,
        question=farmer_input,
        intent=None 
    ) 

    await db.commit()

    return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">{rag_text}</Say>
    <Gather input="speech dtmf"
            action="{NGROK_CONFIRM_ADVISORY}?call_sid={call_session.session_id}"
            method="POST"
            timeout="10"
            speechTimeout="auto"
            numDigits="1"
            language="hi-IN">
        <Say language="hi-IN">क्या यह जानकारी आप सुरक्षित करना चाहेंगे? जानकारी सुरक्षित के लिए एक दबाएँ। अन्यथा, दो दबाएँ।</Say>
    </Gather>
</Response>
''', media_type="text/xml; charset=utf-8")


# ============================================================
# FINAL IMPROVED CONFIRMATION HANDLER FOR ADVISORY SAVE
# Auto-creates CallSession if it doesn't exist
# ============================================================
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.api_route("/twilio/confirm-advisory", methods=["POST"], tags=["Twilio"])
@router.api_route("/api/twilio/confirm-advisory", methods=["POST"], tags=["Twilio"])
async def confirm_advisory(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    call_sid = form.get("CallSid") or request.query_params.get("call_sid")
    confirmation = form.get("Digits")
    phone_number = form.get("From")
    # Fetch the latest farmer profile for this phone number
    result = await db.execute(
        select(Farmer).where(Farmer.phone_number == phone_number).order_by(Farmer.id.desc())
    )
    farmer = result.scalars().first()
    if not farmer:
        # Do not drop call, continue gracefully
        return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">प्रोफ़ाइल नहीं मिली, कृपया फिर से प्रयास करें।</Say>
    <Gather input="speech"
            action="/api/twilio/free-question"
            method="POST"
            timeout="20"
            speechTimeout="auto"
            language="hi-IN">
        <Say language="hi-IN">अगर आपके पास और सवाल है तो पूछें।</Say>
    </Gather>
</Response>
''', media_type="text/xml; charset=utf-8")

    # ============================================================
    # OPTION 1: AUTO-CREATE CallSession if it doesn't exist
    # ============================================================
    session_result = await db.execute(select(CallSession).where(CallSession.session_id == call_sid))
    call_session = session_result.scalars().first()
    
    if not call_session:
        # Create new CallSession
        call_session = CallSession(
            session_id=call_sid,
            phone_number=phone_number,
            farmer_id=farmer.id,
            provider_call_id=call_sid,
        )
        db.add(call_session)
        await db.commit()
        await db.refresh(call_session)
        print(f"CallSession created with id: {call_session.id}")
    
    # Get advisory text from call_session
    ai_response = None
    repeat_count = 0
    
    # Get advisory from advisory_text field (stored in line 264 of your code)
    ai_response = call_session.advisory_text
    
    # Also check provider_name as backup
    if not ai_response and call_session.provider_name and "|AI:" in call_session.provider_name:
        ai_response = call_session.provider_name.split("|AI:")[-1].split("|")[0]
    
    
    farmer_question_text = "No question captured"
    question_result = await db.execute(
        select(FarmerQuestion)
        .where(FarmerQuestion.call_sid == call_sid)
        .order_by(FarmerQuestion.id.desc())
        .limit(1)
    )
    latest_question = question_result.scalars().first()
    if latest_question and latest_question.question_text:
        farmer_question_text = latest_question.question_text

    # Define valid confirmations
    unclear = False
    
    if confirmation != "2" and confirmation != "1":
        
        unclear = True
    
    if unclear and repeat_count < 1:
        # Repeat confirmation prompt once
        new_provider_name = (call_session.provider_name or "")
        if "|CONFIRM_REPEAT:" in new_provider_name:
            new_provider_name = new_provider_name.split("|CONFIRM_REPEAT:")[0]
        new_provider_name += f"|CONFIRM_REPEAT:{repeat_count+1}|"
        call_session.provider_name = new_provider_name
        await db.commit()
    
        return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">माफ़ कीजिए, आपकी पुष्टि स्पष्ट नहीं थी। क्या आप सलाह सुरक्षित करना चाहेंगे? जानकारी सुरक्षित के लिए एक दबाएँ। अन्यथा, दो दबाएँ</Say>
    <Gather input="speech"
            action="/api/twilio/confirm-advisory?call_sid={call_sid}"
            method="POST"
            timeout="10"
            speechTimeout="auto"
            language="hi-IN">
    </Gather>
</Response>
''', media_type="text/xml; charset=utf-8")
    
    # ============================================================
    # MAIN LOGIC: SAVE TO DATABASE ONLY IF CONFIRMATION IS "YES"
    # ============================================================
    save_message = "सलाह सुरक्षित नहीं की गई।"


    # if confirmation in valid_yes:
    if confirmation == "1":
        # User said YES - create case and save advisory
        try:
            # Always create a NEW case for each advisory
            case = Case(
                session_id=call_session.id,  # Now guaranteed to exist
                farmer_id=farmer.id,
                status="OPEN",  # Use enum
                problem_text=farmer_question_text,  # Get from farmer_questions table
                created_at=datetime.utcnow()
            )
            db.add(case)
            await db.commit()
            await db.refresh(case)
            
            # Save advisory if we have advisory text
            if ai_response:
                advisory = Advisory(
                    case_id=case.id,
                    advisory_text_hindi=ai_response,
                    created_at=datetime.utcnow()
                )
                db.add(advisory)
                await db.commit()
                  
            save_message = "सलाह सुरक्षित कर ली गई है।"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            await db.rollback()
            save_message = "सलाह सुरक्षित करने में त्रुटि हुई।"

   
    
    # Reset repeat count and advisory_generated flag in session for next question
    if "|CONFIRM_REPEAT:" in (call_session.provider_name or ""):
        call_session.provider_name = call_session.provider_name.split("|CONFIRM_REPEAT:")[0]
    call_session.advisory_generated = False
    call_session.advisory_text = None
    await db.commit()
    
    # Continue the conversation (always return to free-form Q&A)
    return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">{save_message}</Say>
    <Gather input="speech"
            action="/api/twilio/free-question"
            method="POST"
            timeout="20"
            speechTimeout="auto"
            language="hi-IN">
        <Say language="hi-IN">कृपया अपना अगला सवाल पूछें।</Say>
    </Gather>
</Response>
''', media_type="text/xml; charset=utf-8")





# ============================================================
# INCOMING CALL
# ============================================================

@router.api_route("/twilio/incoming-call", methods=["GET", "POST"], tags=["Twilio"])
@router.api_route("/api/twilio/incoming-call", methods=["GET", "POST"], tags=["Twilio"])
async def twilio_incoming_call(request: Request , db: AsyncSession = Depends(get_db)):
    form = await request.form() if request.method == "POST" else request.query_params
    call_sid = form.get("CallSid")
    phone_number = form.get("From")
    
    if not call_sid:
        return Response("Missing CallSid", status_code=status.HTTP_400_BAD_REQUEST)
    
#     farmer_result = await db.execute(
#         select(Farmer)
#         .where(Farmer.phone_number == phone_number)
#         .order_by(Farmer.id.desc())
#         .limit(1)
#     )
#     existing_farmer = farmer_result.scalars().first()
    
#     if existing_farmer:
#         # Farmer found - get their most recent session
#         session_result = await db.execute(
#             select(CallSession)
#             .where(CallSession.farmer_id == existing_farmer.id)
#             .order_by(CallSession.id.desc())
#             .limit(1)
#         )
#         recent_session = session_result.scalars().first()
        
#         old_session_id = recent_session.session_id if recent_session else call_sid
        
#         logger.info(f"Farmer found with ID: {existing_farmer.id}, Using Session ID: {old_session_id}")
        
#         # Route to free-question endpoint with old session_id
#         return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
# <Response>
#     <Say language="hi-IN">आपका स्वागत है। अब आप अपनी खेती से जुड़ा कोई भी सवाल पूछ सकते हैं।</Say>
#     <Gather input="speech"
#             action="{NGROK_ACTIONN}"
#             method="POST"
#             timeout="20"
#             speechTimeout="auto"
#             actionOnEmptyResult="true"
#             language="hi-IN">
#         <Say language="hi-IN">कृपया अपना सवाल पूछें।</Say>
#     </Gather>
# </Response>
# ''', media_type="text/xml; charset=utf-8")
    
    session_manager.update_step_index(call_sid, 0)
  

    with open(FLOW_PATH, encoding="utf-8") as f:
        flow = json.load(f)

    greeting = flow.get("greeting", "")
    steps = flow.get("steps", [])
    first_question = steps[0]["question"] if steps else "नमस्ते"

    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">{greeting}</Say>
    <Pause length="1"/>
    <Gather input="speech"
            action="{NGROK_ACTION}"
            method="POST"
            timeout="10"
            speechTimeout="auto"
            actionOnEmptyResult="true"
            language="hi-IN">
        <Say language="hi-IN">{first_question}</Say>
    </Gather>
</Response>
'''
    return Response(content=twiml, media_type="text/xml; charset=utf-8")


# ============================================================
# NEXT STEP
# ============================================================

@router.api_route("/twilio/next-step", methods=["POST"], tags=["Twilio"])
@router.api_route("/api/twilio/next-step", methods=["POST"], tags=["Twilio"])
async def twilio_next_step(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()


    call_sid = form.get("CallSid")
    raw_speech = form.get("SpeechResult")
    phone_number = form.get("From")

    if not call_sid:
        return Response("Missing CallSid", status_code=status.HTTP_400_BAD_REQUEST)
    
#      # ============================================================
#     # CHECK IF FARMER EXISTS FIRST - BEFORE ANY FLOW
#     # ============================================================
#     farmer_result = await db.execute(
#         select(Farmer)
#         .where(Farmer.phone_number == phone_number)
#         .order_by(Farmer.id.desc())
#         .limit(1)
#     )
#     existing_farmer = farmer_result.scalars().first()
    
#     if existing_farmer:
#         # Farmer found - get their most recent session
#         session_result = await db.execute(
#             select(CallSession)
#             .where(CallSession.farmer_id == existing_farmer.id)
#             .order_by(CallSession.id.desc())
#             .limit(1)
#         )
#         recent_session = session_result.scalars().first()
        
#         old_session_id = recent_session.session_id if recent_session else call_sid
        
#         logger.info(f"Farmer found with ID: {existing_farmer.id}, Using Session ID: {old_session_id}")
        
#         # Route to free-question endpoint with old session_id
#         return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
# <Response>
#     <Say language="hi-IN">आपका स्वागत है। अब आप अपनी खेती से जुड़ा कोई भी सवाल पूछ सकते हैं।</Say>
#     <Gather input="speech"
#             action="{NGROK_ACTIONN}"
#             method="POST"
#             timeout="20"
#             speechTimeout="auto"
#             actionOnEmptyResult="true"
#             language="hi-IN">
#         <Say language="hi-IN">कृपया अपना सवाल पूछें।</Say>
#     </Gather>
# </Response>
# ''', media_type="text/xml; charset=utf-8")
    
    step_index = session_manager.get_step_index(call_sid)

    with open(FLOW_PATH, encoding="utf-8") as f:
        flow = json.load(f)

    steps = flow["steps"]

    # ============================================================
    # HANDLE TIMEOUT (NO SPEECH RESULT)
    # ============================================================
    if not raw_speech or not raw_speech.strip():
        retry_count = session_manager.get_retry_count(call_sid)
        
        if retry_count == 0:
            # FIRST TIMEOUT: Give warning and repeat question
            session_manager.increment_retry(call_sid)
            current_question = steps[step_index]["question"]
            
            return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">हमें आपकी तरफ से कोई उत्तर नहीं मिला।</Say>
    <Pause length="1"/>
    <Gather input="speech"
            action="{NGROK_ACTION}"
            method="POST"
            timeout="10"
            speechTimeout="auto"
            actionOnEmptyResult="true"
            language="hi-IN">
        <Say language="hi-IN">{current_question}</Say>
    </Gather>
</Response>
''', media_type="text/xml; charset=utf-8")
        
        else:
            # SECOND TIMEOUT: End call and delete incomplete data
            await delete_incomplete_farmer(db, call_sid)
            session_manager.clear_session(call_sid)
            
            return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">आपका कॉल काट दिया जा रहा है।</Say>
    <Hangup/>
</Response>
''', media_type="text/xml; charset=utf-8")

    # ---------------- CLEAN SPEECH ----------------
    speech = clean_speech(raw_speech)

    if not speech:
        return repeat_question(
            steps[step_index]["question"],
            "आपकी आवाज़ स्पष्ट नहीं है। कृपया दोबारा बोलिए।"
        )

    # ---------------- CALL SESSION ----------------
    result = await db.execute(select(CallSession).where(CallSession.session_id == call_sid))
    call_session = result.scalars().first()
    logger.info("searching call session------------------------------------------")


    if not call_session:
        call_session = CallSession(
            session_id=call_sid,
            phone_number=phone_number,
            provider_call_id=call_sid
        )
        logger.info("storing call session--------------------------------")
        db.add(call_session)
        await db.commit()
        await db.refresh(call_session)

    # ---------------- STRICT ONE FARMER PER CALL ----------------

    farmer = None
    if call_session.farmer_id:
        logger.info("call session.farmer_id--------------------------------------------")
        # Always use the farmer attached to this call session
        farmer_result = await db.execute(select(Farmer).where(Farmer.id == call_session.farmer_id))
        farmer = farmer_result.scalars().first()
        logger.info("farmer found--------------------------------------------------")
    
    else:
            
        logger.info("farmer not found---------------------------")
        farmer = Farmer(phone_number=phone_number, status="ACTIVE")
        db.add(farmer)
        logger.info("farmer stored and added to database------------------")
        await db.commit()
        await db.refresh(farmer)
        call_session.farmer_id = farmer.id
        logger.info("call session.farmerid is now farmer.id------------------------------")
        await db.commit()
        
    logger.info("flow go an as it is....-----------------------------------------")
    # ---------------- VALIDATE + SAVE ----------------
    field = steps[step_index]["field"]
    if not validate_answer(field, speech):
        return repeat_question(
            steps[step_index]["question"],
            "सही जानकारी समझ नहीं आई। कृपया साफ और सही जवाब दें।"
        )
        
    setattr(farmer, field, speech)
    await db.commit()

    # ---------------- TRANSCRIPT ----------------
    transcript = CallTranscript(
        call_session_id=call_session.id,
        speaker=Speaker.FARMER,
        transcript_text=speech,
        language_code="hi-IN",
        spoken_at=datetime.utcnow()
    )
    db.add(transcript)
    await db.commit()

    # ---------------- NEXT STEP ----------------
    next_index = step_index + 1
    session_manager.update_step_index(call_sid, next_index)

    # Check if we've completed all questions
    if next_index >= len(steps):
        # Profile is complete - transition to freeform mode
        session_manager.clear_session(call_sid)
        
        freeform_message = "अब आप अपनी खेती से जुड़ा कोई भी सवाल पूछ सकते हैं।"
        return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">{freeform_message}</Say>
    <Gather input="speech"
            action="{NGROK_ACTIONN}"
            method="POST"
            timeout="20"
            speechTimeout="auto"
            actionOnEmptyResult="true"
            language="hi-IN">
        <Say language="hi-IN">कृपया अपना सवाल पूछें।</Say>
    </Gather>
</Response>
''', media_type="text/xml; charset=utf-8")

    # Continue to next question
    next_question = steps[next_index]["question"]
    return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech"
            action="{NGROK_ACTION}"
            method="POST"
            timeout="10"
            speechTimeout="auto"
            actionOnEmptyResult="true"
            language="hi-IN">
        <Say language="hi-IN">{next_question}</Say>
    </Gather>
</Response>
''', media_type="text/xml; charset=utf-8")




