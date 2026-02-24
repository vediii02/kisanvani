"""
Test API Routes - For Interactive Testing Form
Provides endpoints to test farmer information collection step by step
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from api.deps import get_db
from db.models.farmer import Farmer
from db.models.call_session import CallSession, CallStatus
from db.models.case import Case, CaseStatus
from db.models.advisory import Advisory
from services.gemini_advisory_service import gemini_advisory_service
from nlu.intent import detect_intent
import nlu.entity_extractor as entity_extractor

router = APIRouter(prefix="/test", tags=["test"])


class StartCallRequest(BaseModel):
    phone_number: str


class UpdateFarmerRequest(BaseModel):
    farmer_id: int
    field: str
    value: str


class SaveQuestionRequest(BaseModel):
    call_session_id: int
    farmer_id: int
    question: str
    affected_area_acres: Optional[float] = None


class EndCallRequest(BaseModel):
    call_session_id: int
    status: str


@router.post("/start-call")
async def start_call(request: StartCallRequest, db: AsyncSession = Depends(get_db)):
    """
    Step 1: Start a call and create farmer + call session
    """
    try:
            # Check if farmer exists
        result = await db.execute(
            select(Farmer).where(Farmer.phone_number == request.phone_number)
        )
        farmer = result.scalar_one_or_none()
        
        # Create new farmer if doesn't exist
        if not farmer:
            farmer = Farmer(
                phone_number=request.phone_number,
                language='hi'
            )
            db.add(farmer)
            await db.commit()
            await db.refresh(farmer)
        
        # Create call session
        call_session = CallSession(
            session_id=f"test_{int(datetime.now(timezone.utc).timestamp())}",
            farmer_id=farmer.id,
            phone_number=request.phone_number,
            status=CallStatus.ACTIVE
        )
        db.add(call_session)
        await db.commit()
        await db.refresh(call_session)
        
        return {
            "success": True,
            "farmer_id": farmer.id,
            "call_session_id": call_session.id,
            "message": "Call started successfully"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-farmer")
async def update_farmer(request: UpdateFarmerRequest, db: AsyncSession = Depends(get_db)):
    """
    Update farmer field by field
    """
    try:
        farmer = await db.get(Farmer, request.farmer_id)
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        # Update the specific field
        setattr(farmer, request.field, request.value)
        await db.commit()
        await db.refresh(farmer)
        
        return {
            "success": True,
            "field": request.field,
            "value": request.value,
            "message": f"{request.field} updated successfully"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-question")
async def save_question(request: SaveQuestionRequest, db: AsyncSession = Depends(get_db)):
    """
    Save farmer's question and generate AI response using RAG
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    try:
        # Get farmer details
        farmer = await db.get(Farmer, request.farmer_id)
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        # Detect intent
        try:
            intent_result = detect_intent(request.question)
            intent = intent_result.get("intent", "crop_disease")
        except Exception as e:
            logger.error(f"Intent detection error: {str(e)}")
            intent = "crop_disease"
        
        # Extract entities
        try:
            entities = entity_extractor.extract_all_farmer_entities(request.question)
        except Exception as e:
            logger.error(f"Entity extraction error: {str(e)}")
            entities = {}
        
        # Add farmer context including crop area
        if farmer.crop_type and not entities.get("crop"):
            entities["crop"] = farmer.crop_type
        
        # Get crop area from farmer table
        crop_area_acres = getattr(farmer, 'crop_area_acres', None)
        affected_area = request.affected_area_acres
        
        context = {
            "crop": farmer.crop_type,
            "land_size": farmer.land_size,
            "crop_area_acres": crop_area_acres,
            "affected_area_acres": affected_area,
            "village": farmer.village,
            "district": farmer.district,
            "state": farmer.state
        }
        
        # Add area context to query for better AI response
        enhanced_query = request.question
        if crop_area_acres and affected_area:
            percentage_affected = (affected_area / crop_area_acres) * 100
            enhanced_query = f"{request.question} (कुल फसल क्षेत्र: {crop_area_acres} एकड़, प्रभावित क्षेत्र: {affected_area} एकड़, {percentage_affected:.1f}% प्रभावित)"
        elif affected_area:
            enhanced_query = f"{request.question} (प्रभावित क्षेत्र: {affected_area} एकड़)"
        
        # Generate AI response using Gemini
        response_text = None
        try:
            advisory_result = await gemini_advisory_service.generate_advisory(
                farmer_query=enhanced_query,
                session_id=str(request.call_session_id)
            )
            
            if advisory_result:
                response_text = advisory_result.get("advisory_text")
                
                # Add area-specific recommendations if applicable
                if affected_area and crop_area_acres:
                    percentage_affected = (affected_area / crop_area_acres) * 100
                    if percentage_affected < 25:
                        response_text += f"\n\n💡 क्षेत्र विश्लेषण: समस्या केवल {percentage_affected:.1f}% क्षेत्र ({affected_area} एकड़) में है। तुरंत उपचार करें ताकि बाकी फसल सुरक्षित रहे।"
                    elif percentage_affected < 50:
                        response_text += f"\n\n⚠️ क्षेत्र विश्लेषण: {percentage_affected:.1f}% क्षेत्र ({affected_area} एकड़) प्रभावित है। जल्दी उपचार जरूरी है।"
                    else:
                        response_text += f"\n\n🚨 क्षेत्र विश्लेषण: {percentage_affected:.1f}% क्षेत्र ({affected_area} एकड़) प्रभावित है। व्यापक उपचार की जरूरत है। विशेषज्ञ से सलाह लें।"
                
                logger.info(f"Advisory generated. Area: {affected_area} acres, Confidence: {advisory_result.get('confidence')}")
        except Exception as e:
            logger.error(f"Advisory service error: {str(e)}\n{traceback.format_exc()}")
        
        # Use fallback response if RAG failed
        if not response_text:
            response_text = "आपके सवाल के लिए धन्यवाद। हमारे विशेषज्ञ जल्द ही आपसे संपर्क करेंगे।"
        
        # Create case (without affected_area for now)
        case = Case(
            session_id=request.call_session_id,
            farmer_id=request.farmer_id,
            problem_text=request.question,
            problem_category=intent,
            crop_name=entities.get("crop", farmer.crop_type),
            status=CaseStatus.RESOLVED
        )
        db.add(case)
        await db.commit()
        await db.refresh(case)
        
        # Save advisory
        advisory = Advisory(
            case_id=case.id,
            advisory_text_hindi=response_text,
            was_escalated=False
        )
        db.add(advisory)
        await db.commit()
        
        return {
            "success": True,
            "case_id": case.id,
            "question": request.question,
            "response": response_text,
            "affected_area": affected_area,
            "crop_area": crop_area_acres,
            "intent": intent,
            "entities": entities,
            "message": "Question and AI response saved"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in save_question: {str(e)}\n{traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/end-call")
async def end_call(request: EndCallRequest, db: AsyncSession = Depends(get_db)):
    """
    End call and update status
    """
    try:
        call_session = await db.get(CallSession, request.call_session_id)
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        call_session.status = CallStatus[request.status]
        call_session.end_time = datetime.now(timezone.utc)
        
        if call_session.start_time and call_session.end_time:
            duration = (call_session.end_time - call_session.start_time).total_seconds()
            call_session.duration_seconds = int(duration)
        
        await db.commit()
        
        return {
            "success": True,
            "status": request.status,
            "message": "Call ended successfully"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/view-data/{farmer_id}")
async def view_data(farmer_id: int, db: AsyncSession = Depends(get_db)):
    """
    View all saved data for a farmer
    """
    try:
        # Get farmer
        farmer = await db.get(Farmer, farmer_id)
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        # Get call sessions
        result = await db.execute(
            select(CallSession).where(CallSession.farmer_id == farmer_id)
        )
        call_sessions = result.scalars().all()
        
        # Get latest call session
        latest_session = call_sessions[-1] if call_sessions else None
        
        # Get cases and advisories
        cases_data = []
        if latest_session:
            result = await db.execute(
                select(Case).where(Case.session_id == latest_session.id)
            )
            cases = result.scalars().all()
            
            for case in cases:
                result = await db.execute(
                    select(Advisory).where(Advisory.case_id == case.id)
                )
                advisory = result.scalar_one_or_none()
                
                cases_data.append({
                    "problem_text": case.problem_text,
                    "problem_category": case.problem_category,
                    "crop_name": case.crop_name,
                    "status": case.status.value,
                    "advisory": {
                        "advisory_text_hindi": advisory.advisory_text_hindi
                    } if advisory else None
                })
        
        return {
            "farmer": {
                "id": farmer.id,
                "phone_number": farmer.phone_number,
                "name": farmer.name,
                "village": farmer.village,
                "district": farmer.district,
                "state": farmer.state,
                "crop_type": farmer.crop_type,
                "land_size": farmer.land_size
            },
            "call_session": {
                "id": latest_session.id,
                "session_id": latest_session.session_id,
                "status": latest_session.status.value,
                "start_time": latest_session.start_time.isoformat(),
                "end_time": latest_session.end_time.isoformat() if latest_session.end_time else None,
                "duration_seconds": latest_session.duration_seconds
            } if latest_session else None,
            "cases": cases_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
