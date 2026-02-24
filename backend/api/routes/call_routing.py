"""
Incoming Call API - Multi-Tenant Call Routing

This endpoint handles ALL incoming calls (simulator or real Exotel).
Routes calls to correct organisation based on dialed phone number.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from db.session import get_db
from services.call_routing_service import call_routing_service
from services.conversation_manager import conversation_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/call-routing", tags=["Call Routing"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class IncomingCallRequest(BaseModel):
    """
    Schema for incoming call payload.
    
    Works for BOTH:
    1. Simulator/Test calls from frontend
    2. Real Exotel webhook calls
    """
    from_phone: str = Field(..., description="Caller's phone number (farmer)")
    to_phone: str = Field(..., description="Dialed phone number (organisation's number)")
    call_id: Optional[str] = Field(None, description="External call ID (Exotel/simulator)")
    source: str = Field(default="simulator", description="Call source: simulator, exotel, etc.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional call metadata")


class IncomingCallResponse(BaseModel):
    """Response after successful call routing"""
    success: bool
    call_session_id: int
    organisation_id: int
    organisation_name: str
    greeting_message: str
    language: str
    farmer_id: int
    message: str


class CallRejectionResponse(BaseModel):
    """Response when call is rejected"""
    success: bool = False
    error: str
    rejection_message: str
    suggestion: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/incoming", response_model=IncomingCallResponse)
async def handle_incoming_call(
    call_request: IncomingCallRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming call and route to correct organisation.
    
    **This is the ENTRY POINT for all calls in the system.**
    
    **Flow:**
    1. Farmer calls organisation's phone number (e.g., 9999888877)
    2. System receives: from_phone (farmer) and to_phone (org number)
    3. Lookup organisation using to_phone
    4. If found: Create call session, return greeting
    5. If not found: Reject call with polite message
    
    **Key Features:**
    - Works with simulator (frontend form) OR real Exotel webhooks
    - No difference in logic - same routing for both
    - Farmer NEVER asked which organisation they belong to
    - Organisation identified ONLY by to_phone
    
    **Example Request (Simulator):**
    ```json
    {
      "from_phone": "+919876543210",
      "to_phone": "9999888877",
      "source": "simulator"
    }
    ```
    
    **Example Request (Exotel):**
    ```json
    {
      "from_phone": "+919876543210",
      "to_phone": "9999888877",
      "call_id": "123abc",
      "source": "exotel",
      "metadata": {"duration": 0, "status": "ringing"}
    }
    ```
    
    **Success Response:**
    ```json
    {
      "success": true,
      "call_session_id": 42,
      "organisation_id": 1,
      "organisation_name": "Ankur Seeds",
      "greeting_message": "नमस्ते, आप Ankur Seeds किसान सहायक AI से बात कर रहे हैं",
      "language": "hi",
      "farmer_id": 123,
      "message": "Call routed successfully"
    }
    ```
    
    **Rejection Response:**
    ```json
    {
      "success": false,
      "error": "No active organisation found for phone number 9999888877",
      "rejection_message": "क्षमा करें, यह नंबर वर्तमान में सेवा में नहीं है",
      "suggestion": "कृपया सही नंबर डायल करें"
    }
    ```
    """
    logger.info(
        f"Incoming call request: from={call_request.from_phone}, "
        f"to={call_request.to_phone}, source={call_request.source}"
    )
    
    # Prepare call metadata
    call_metadata = call_request.metadata or {}
    call_metadata['call_id'] = call_request.call_id
    call_metadata['source'] = call_request.source
    
    # Route the call using call routing service
    call_session, organisation, error = await call_routing_service.handle_incoming_call(
        db=db,
        from_phone=call_request.from_phone,
        to_phone=call_request.to_phone,
        call_metadata=call_metadata
    )
    
    # If routing failed, return rejection response
    if error:
        logger.warning(f"Call routing failed: {error}")
        
        # Determine appropriate rejection message based on error
        if "not found" in error.lower():
            rejection_msg = "क्षमा करें, यह नंबर वर्तमान में सेवा में नहीं है। कृपया सही नंबर डायल करें।"
            suggestion = "Please check the number and try again"
        elif "not active" in error.lower():
            rejection_msg = "क्षमा करें, यह सेवा अस्थायी रूप से उपलब्ध नहीं है। कृपया कुछ देर बाद पुनः प्रयास करें।"
            suggestion = "Service temporarily unavailable"
        else:
            rejection_msg = "क्षमा करें, कॉल कनेक्ट नहीं हो सकी। कृपया बाद में पुनः प्रयास करें।"
            suggestion = "Technical issue, please try again later"
        
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": error,
                "rejection_message": rejection_msg,
                "suggestion": suggestion
            }
        )
    
    # Get organisation-specific greeting
    greeting = await call_routing_service.get_organisation_greeting(
        db=db,
        organisation_id=organisation.id,
        language=None  # Will use default from organisation
    )
    
    logger.info(
        f"Call routed successfully: CallSession={call_session.id}, "
        f"Org={organisation.name}, Farmer={call_session.farmer_id}"
    )
    
    return IncomingCallResponse(
        success=True,
        call_session_id=call_session.id,
        organisation_id=organisation.id,
        organisation_name=organisation.name,
        greeting_message=greeting,
        language=organisation.preferred_languages.split(',')[0] if organisation.preferred_languages else "hi",
        farmer_id=call_session.farmer_id,
        message=f"Call routed to {organisation.name}"
    )


@router.get("/context/{call_session_id}")
async def get_call_context(
    call_session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete context for an active call session.
    
    **Use Cases:**
    1. AI needs to know which organisation's data to use
    2. Load organisation-specific products
    3. Get farmer's history with this organisation
    4. Determine which knowledge base to query
    
    **Response:**
    ```json
    {
      "call_session": {
        "id": 42,
        "status": "active",
        "language": "hi"
      },
      "organisation": {
        "id": 1,
        "name": "Ankur Seeds",
        "preferred_languages": "hi,en",
        "greeting_message": "Custom greeting..."
      },
      "farmer": {
        "id": 123,
        "phone_number": "+919876543210",
        "name": "Ram Kumar",
        "language": "hi"
      },
      "phone_record": {
        "phone_number": "9999888877",
        "region": "All India",
        "display_name": "Main Helpline"
      }
    }
    ```
    """
    context = await call_routing_service.get_call_context(
        db=db,
        call_session_id=call_session_id
    )
    
    if not context:
        raise HTTPException(
            status_code=404,
            detail="Call session not found"
        )
    
    return context


@router.post("/test-routing")
async def test_phone_routing(
    to_phone: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Test endpoint to verify phone number routing without creating a call.
    
    **Developer Use Case:**
    Quickly check if a phone number is configured correctly.
    
    **Example:**
    ```
    POST /api/call-routing/test-routing?to_phone=9999888877
    ```
    
    **Response:**
    ```json
    {
      "phone_number": "9999888877",
      "is_configured": true,
      "organisation_id": 1,
      "organisation_name": "Ankur Seeds",
      "organisation_status": "active",
      "phone_status": "active",
      "region": "All India",
      "display_name": "Main Helpline"
    }
    ```
    """
    from services.phone_number_service import phone_number_service
    from db.models.organisation import Organisation
    from sqlalchemy import select
    
    org_id, phone_record, error = await phone_number_service.find_organisation_by_phone(
        db=db,
        phone_number=to_phone,
        require_active=False  # Show even if inactive
    )
    
    if error:
        return {
            "phone_number": to_phone,
            "is_configured": False,
            "error": error,
            "message": "Phone number not configured in system"
        }
    
    # Get organisation details
    org_result = await db.execute(
        select(Organisation).where(Organisation.id == org_id)
    )
    organisation = org_result.scalar_one()
    
    return {
        "phone_number": phone_record.phone_number,
        "is_configured": True,
        "organisation_id": org_id,
        "organisation_name": organisation.name,
        "organisation_status": organisation.status,
        "phone_status": "active" if phone_record.is_active else "inactive",
        "region": phone_record.region,
        "display_name": phone_record.display_name,
        "message": "Phone number is properly configured"
    }


# ============================================================================
# Option C: AI Conversation Integration with Call Flow
# ============================================================================

class AIConversationRequest(BaseModel):
    """Request to start AI conversation after call is routed"""
    call_session_id: int
    initial_message: Optional[str] = None


class AIConversationResponse(BaseModel):
    """AI conversation response"""
    success: bool
    message: str
    state: str
    suggestions: Optional[list] = None
    confidence: Optional[float] = None


@router.post("/ai-conversation/start", response_model=AIConversationResponse)
async def start_ai_conversation(
    request: AIConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **Option C: Start AI-powered conversation after call routing**
    
    This integrates the conversation_manager (NLU + RAG + LLM) 
    into the existing call flow.
    
    **Flow:**
    1. Call is routed via /incoming endpoint
    2. Frontend/Exotel calls this endpoint with call_session_id
    3. AI starts conversation with personalized greeting
    4. Returns greeting + initial questions
    
    **Example:**
    ```
    POST /api/call-routing/ai-conversation/start
    {
      "call_session_id": 42
    }
    ```
    
    **Response:**
    ```json
    {
      "success": true,
      "message": "नमस्ते! मैं आपकी फसल की समस्याओं में मदद के लिए यहाँ हूँ। कृपया बताएं, आप किस फसल के बारे में पूछना चाहते हैं?",
      "state": "INITIAL",
      "suggestions": ["धान", "गेहूं", "मक्का", "कपास"]
    }
    ```
    """
    try:
        # Start conversation
        result = await conversation_manager.start_conversation(
            db=db,
            call_session_id=request.call_session_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start conversation: {result.get('error', 'Unknown error')}"
            )
        
        return AIConversationResponse(
            success=True,
            message=result.get("message", ""),  # Fixed: use "message" key
            state=result.get("state", "INITIAL"),
            suggestions=result.get("suggestions", [])
        )
        
    except Exception as e:
        logger.error(f"Error starting AI conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-conversation/message", response_model=AIConversationResponse)
async def process_ai_conversation_message(
    call_session_id: int,
    message: str,
    db: AsyncSession = Depends(get_db)
):
    """
    **Option C: Process farmer's message in AI conversation**
    
    Handles farmer's response during conversation:
    - Detects intent (crop disease, pest, etc.)
    - Extracts entities (crop name, problem, severity)
    - Updates conversation state
    - Generates intelligent response using RAG + LLM
    
    **Example:**
    ```
    POST /api/call-routing/ai-conversation/message?call_session_id=42&message=मेरी धान की फसल में कीड़े लग गए हैं
    ```
    
    **Response:**
    ```json
    {
      "success": true,
      "message": "मुझे समझ आ गया कि आपकी धान की फसल में कीट की समस्या है...",
      "state": "PROVIDING_SOLUTION",
      "confidence": 0.85,
      "suggestions": ["क्या आपको और जानकारी चाहिए?", "क्या खाद के बारे में पूछना है?"]
    }
    ```
    """
    try:
        # Process message
        result = await conversation_manager.process_message(
            db=db,
            call_session_id=call_session_id,
            farmer_message=message
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process message: {result.get('error', 'Unknown error')}"
            )
        
        return AIConversationResponse(
            success=True,
            message=result.get("message", ""),
            state=result.get("state", ""),
            suggestions=result.get("suggestions", []),
            confidence=result.get("confidence")
        )
        
    except Exception as e:
        logger.error(f"Error processing AI message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
