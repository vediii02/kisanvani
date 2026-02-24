"""
Conversation Manager Service
Handles multi-turn text conversations with farmers
Integrates NLU, RAG, and LLM for intelligent responses
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.call_session import CallSession
from db.models.farmer import Farmer
from db.models.organisation import Organisation
from services.gemini_advisory_service import GeminiAdvisoryService as AdvisoryService
from nlu.intent import detect_intent
import nlu.entity_extractor as entity_extractor
import json

logger = logging.getLogger(__name__)


class ConversationState:
    """Track conversation state for a session"""
    
    INITIAL = "initial"
    GATHERING_INFO = "gathering_info"
    UNDERSTANDING_PROBLEM = "understanding_problem"
    PROVIDING_SOLUTION = "providing_solution"
    FOLLOWUP = "followup"
    COMPLETED = "completed"
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = self.INITIAL
        self.context = {
            "crop": None,
            "problem": None,
            "area": None,
            "severity": None,
            "history": []
        }
        self.turn_count = 0


class ConversationManager:
    """
    Manages text-based conversations with farmers
    Flow: Greeting → Info Gathering → Problem Understanding → Solution → Followup
    """
    
    def __init__(self):
        self.advisory_service = AdvisoryService()
        self.sessions: Dict[str, ConversationState] = {}
    
    def _get_or_create_session(self, session_id: str) -> ConversationState:
        """Get or create conversation state"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationState(session_id)
        return self.sessions[session_id]
    
    async def start_conversation(
        self,
        db: AsyncSession,
        call_session_id: int,
        organisation_name: str = None
    ) -> Dict[str, Any]:
        """
        Start a new conversation
        Returns initial greeting
        """
        session_state = self._get_or_create_session(str(call_session_id))
        session_state.state = ConversationState.INITIAL
        
        greeting = self._generate_greeting(organisation_name)
        
        return {
            "success": True,
            "message": greeting,
            "state": session_state.state,
            "next_expected": "crop_name",
            "suggestions": ["मेरी फसल में कीड़े लग गए हैं", "धान की खेती के बारे में जानना है", "खाद की सलाह चाहिए"]
        }
    
    async def process_message(
        self,
        db: AsyncSession,
        call_session_id: int,
        farmer_message: str
    ) -> Dict[str, Any]:
        """
        Process farmer's text message and generate response
        
        Flow:
        1. Get conversation state
        2. Extract intent and entities
        3. Update context
        4. Save farmer information to database
        5. Generate appropriate response based on state
        6. Return response with next steps
        """
        try:
            session_state = self._get_or_create_session(str(call_session_id))
            
            # Validate message - check if empty or too short
            if not farmer_message or len(farmer_message.strip()) < 2:
                return {
                    "success": True,
                    "message": "मुझे आपकी बात समझ नहीं आई। कृपया अपनी समस्या के बारे में बताएं।",
                    "state": session_state.state,
                    "retry": True,
                    "suggestions": self._get_state_suggestions(session_state.state)
                }
            
            # Check for repeat/clarification keywords
            repeat_keywords = ["dobara", "दोबारा", "फिर से", "phir se", "repeat", "समझ नहीं आया", "samajh nahi aaya", "sunai nahi diya", "kya bola", "क्या बोला"]
            if any(keyword in farmer_message.lower() for keyword in repeat_keywords):
                # Get last AI response from history
                last_ai_message = None
                for entry in reversed(session_state.context["history"]):
                    if entry["role"] == "assistant":
                        last_ai_message = entry["message"]
                        break
                
                if last_ai_message:
                    return {
                        "success": True,
                        "message": f"मैं दोबारा बता रहा हूं: {last_ai_message}",
                        "state": session_state.state,
                        "repeated": True
                    }
                else:
                    return {
                        "success": True,
                        "message": "आप मुझसे अपनी फसल की समस्या के बारे में पूछ सकते हैं। कृपया बताएं।",
                        "state": session_state.state
                    }
            
            # Check if message is too short/unclear
            if len(farmer_message.strip()) < 5:
                session_state.turn_count += 1
                return {
                    "success": True,
                    "message": "कृपया थोड़ा विस्तार से बताएं। आप क्या जानना चाहते हैं?",
                    "state": session_state.state,
                    "retry": True,
                    "context": session_state.context
                }
            
            session_state.turn_count += 1
            
            # Add to history
            session_state.context["history"].append({
                "turn": session_state.turn_count,
                "role": "farmer",
                "message": farmer_message
            })
            
            # Extract intent and entities
            intent = await self._classify_intent(farmer_message)
            entities = await self._extract_entities(farmer_message)
            
            logger.info(f"Session {call_session_id}: Intent={intent}, Entities={entities}")
            
            # Update context with extracted entities
            self._update_context(session_state, entities)
            
            # Save farmer information to database if any entities were extracted
            await self._save_farmer_information(db, call_session_id, entities)
            
            # Generate response based on current state and intent
            response = await self._generate_response(
                db=db,
                session_state=session_state,
                call_session_id=call_session_id,
                farmer_message=farmer_message,
                intent=intent,
                entities=entities
            )
            
            # Add response to history
            session_state.context["history"].append({
                "turn": session_state.turn_count,
                "role": "assistant",
                "message": response["message"]
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "message": "क्षमा करें, कुछ गलती हो गई। कृपया दोबारा कोशिश करें।",
                "error": str(e)
            }
            
            # Check for repeat/clarification keywords
            repeat_keywords = ["dobara", "दोबारा", "फिर से", "phir se", "repeat", "समझ नहीं आया", "samajh nahi aaya", "sunai nahi diya", "kya bola", "क्या बोला"]
            if any(keyword in farmer_message.lower() for keyword in repeat_keywords):
                # Get last AI response from history
                last_ai_message = None
                for entry in reversed(session_state.context["history"]):
                    if entry["role"] == "assistant":
                        last_ai_message = entry["message"]
                        break
                
                if last_ai_message:
                    return {
                        "success": True,
                        "message": f"मैं दोबारा बता रहा हूं: {last_ai_message}",
                        "state": session_state.state,
                        "repeated": True
                    }
                else:
                    return {
                        "success": True,
                        "message": "आप मुझसे अपनी फसल की समस्या के बारे में पूछ सकते हैं। कृपया बताएं।",
                        "state": session_state.state
                    }
            
            # Check if message is too short/unclear
            if len(farmer_message.strip()) < 5:
                session_state.turn_count += 1
                return {
                    "success": True,
                    "message": "कृपया थोड़ा विस्तार से बताएं। आप क्या जानना चाहते हैं?",
                    "state": session_state.state,
                    "retry": True,
                    "context": session_state.context
                }
            
            session_state.turn_count += 1
            
            # Add to history
            session_state.context["history"].append({
                "turn": session_state.turn_count,
                "role": "farmer",
                "message": farmer_message
            })
            
            # Extract intent and entities
            intent = await self._classify_intent(farmer_message)
            entities = await self._extract_entities(farmer_message)
            
            logger.info(f"Session {call_session_id}: Intent={intent}, Entities={entities}")
            
            # Update context with extracted entities
            self._update_context(session_state, entities)
            
            # Generate response based on current state and intent
            response = await self._generate_response(
                db=db,
                session_state=session_state,
                call_session_id=call_session_id,
                farmer_message=farmer_message,
                intent=intent,
                entities=entities
            )
            
            # Add response to history
            session_state.context["history"].append({
                "turn": session_state.turn_count,
                "role": "assistant",
                "message": response["message"]
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "message": "क्षमा करें, कुछ गलती हो गई। कृपया दोबारा कोशिश करें।",
                "error": str(e)
            }
    
    async def _classify_intent(self, message: str) -> str:
        """Classify farmer's intent"""
        try:
            intent = detect_intent(message)
            return intent
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return "general_query"
    
    async def _save_farmer_information(
        self,
        db: AsyncSession,
        call_session_id: int,
        entities: Dict[str, Any]
    ):
        """
        Save extracted farmer information to database.
        Updates farmer record with any new information collected during conversation.
        """
        try:
            # Get call session to find farmer
            result = await db.execute(
                select(CallSession).where(CallSession.id == call_session_id)
            )
            call_session = result.scalar_one_or_none()
            
            if not call_session or not call_session.farmer_id:
                logger.warning(f"Call session {call_session_id} or farmer not found")
                return
            
            # Get farmer record
            farmer = await db.get(Farmer, call_session.farmer_id)
            if not farmer:
                logger.warning(f"Farmer {call_session.farmer_id} not found")
                return
            
            # Update farmer fields with extracted information
            updated = False
            
            if entities.get('name') and not farmer.name:
                farmer.name = entities['name']
                updated = True
                logger.info(f"Updated farmer name: {entities['name']}")
            
            if entities.get('village') and not farmer.village:
                farmer.village = entities['village']
                updated = True
                logger.info(f"Updated farmer village: {entities['village']}")
            
            if entities.get('district') and not farmer.district:
                farmer.district = entities['district']
                updated = True
                logger.info(f"Updated farmer district: {entities['district']}")
            
            if entities.get('state') and not farmer.state:
                farmer.state = entities['state']
                updated = True
                logger.info(f"Updated farmer state: {entities['state']}")
            
            if entities.get('crop_type') and not farmer.crop_type:
                farmer.crop_type = entities['crop_type']
                updated = True
                logger.info(f"Updated farmer crop_type: {entities['crop_type']}")
            
            if entities.get('land_size') and not farmer.land_size:
                farmer.land_size = entities['land_size']
                updated = True
                logger.info(f"Updated farmer land_size: {entities['land_size']}")
            
            # Add crop_age_days if present in entities
            if entities.get('crop_age_days') is not None:
                try:
                    crop_age_val = int(entities['crop_age_days'])
                    if (farmer.crop_age_days is None) or (farmer.crop_age_days != crop_age_val):
                        farmer.crop_age_days = crop_age_val
                        updated = True
                        logger.info(f"Updated farmer crop_age_days: {crop_age_val}")
                except Exception as e:
                    logger.warning(f"Could not parse crop_age_days: {entities['crop_age_days']} - {e}")

            # Commit changes if any updates were made
            if updated:
                await db.commit()
                await db.refresh(farmer)
                logger.info(f"✅ Farmer information saved successfully for farmer_id={farmer.id}")
            
        except Exception as e:
            logger.error(f"Error saving farmer information: {e}", exc_info=True)
            # Don't raise exception - continue conversation even if save fails
            await db.rollback()
    
    async def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from message"""
        try:
            # Use entity_extractor module functions to extract all farmer information
            entities = entity_extractor.extract_all_farmer_entities(message)
            
            # Also extract individual entities for backward compatibility
            crop = entity_extractor.extract_crop(message)
            if crop:
                entities["crop"] = crop
            
            return entities
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return {}
    
    def _update_context(self, session_state: ConversationState, entities: Dict[str, Any]):
        """Update conversation context with new entities"""
        if "crop" in entities and entities["crop"]:
            session_state.context["crop"] = entities["crop"]
        if "problem" in entities and entities["problem"]:
            session_state.context["problem"] = entities["problem"]
        if "area" in entities and entities["area"]:
            session_state.context["area"] = entities["area"]
        
        # Store farmer personal information
        if "name" in entities and entities["name"]:
            session_state.context["farmer_name"] = entities["name"]
        if "village" in entities and entities["village"]:
            session_state.context["farmer_village"] = entities["village"]
        if "district" in entities and entities["district"]:
            session_state.context["farmer_district"] = entities["district"]
        if "state" in entities and entities["state"]:
            session_state.context["farmer_state"] = entities["state"]
        if "crop_type" in entities and entities["crop_type"]:
            session_state.context["farmer_crop_type"] = entities["crop_type"]
        if "land_size" in entities and entities["land_size"]:
            session_state.context["farmer_land_size"] = entities["land_size"]
    
    async def _generate_response(
        self,
        db: AsyncSession,
        session_state: ConversationState,
        call_session_id: int,
        farmer_message: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate appropriate response based on state and intent"""
        
        # State-based response generation
        if session_state.state == ConversationState.INITIAL:
            return await self._handle_initial_state(session_state, farmer_message, entities)
        
        elif session_state.state == ConversationState.GATHERING_INFO:
            return await self._handle_gathering_info(session_state, farmer_message, entities)
        
        elif session_state.state == ConversationState.UNDERSTANDING_PROBLEM:
            return await self._handle_understanding_problem(session_state, farmer_message, entities)
        
        elif session_state.state == ConversationState.PROVIDING_SOLUTION:
            return await self._handle_providing_solution(session_state, farmer_message, entities, call_session_id)
        
        elif session_state.state == ConversationState.FOLLOWUP:
            return await self._handle_followup(session_state, farmer_message, entities)
        
        else:
            # Default: try to provide solution
            return await self._handle_providing_solution(session_state, farmer_message, entities, call_session_id)
    
    async def _handle_initial_state(
        self,
        session_state: ConversationState,
        message: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle initial state - gather basic info"""
        
        if session_state.context["crop"] and session_state.context["problem"]:
            # Have enough info, move to solution
            session_state.state = ConversationState.PROVIDING_SOLUTION
            return {
                "success": True,
                "message": f"अच्छा, तो आपकी {session_state.context['crop']} की फसल में {session_state.context['problem']} की समस्या है। मैं आपके लिए समाधान ढूंढ रहा हूं...",
                "state": session_state.state,
                "context": session_state.context
            }
        
        elif session_state.context["crop"]:
            # Have crop, need problem
            session_state.state = ConversationState.GATHERING_INFO
            return {
                "success": True,
                "message": f"आपकी {session_state.context['crop']} की फसल में क्या समस्या है? कृपया विस्तार से बताएं।",
                "state": session_state.state,
                "next_expected": "problem_description"
            }
        
        else:
            # Need crop info
            session_state.state = ConversationState.GATHERING_INFO
            return {
                "success": True,
                "message": "आप किस फसल के बारे में जानना चाहते हैं?",
                "state": session_state.state,
                "next_expected": "crop_name",
                "suggestions": ["धान", "गेहूं", "कपास", "टमाटर", "प्याज"]
            }
    
    async def _handle_gathering_info(
        self,
        session_state: ConversationState,
        message: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gather crop and problem information"""
        
        # Check if no entities extracted - farmer's response is unclear
        if not entities or (not entities.get("crop") and not session_state.context["crop"]):
            return {
                "success": True,
                "message": "मुझे आपकी फसल का नाम समझ नहीं आया। कृपया बताएं - धान, गेहूं, कपास, टमाटर या कोई और फसल?",
                "state": session_state.state,
                "retry": True,
                "suggestions": ["धान", "गेहूं", "कपास", "टमाटर", "मिर्च", "प्याज"]
            }
        
        if session_state.context["crop"] and session_state.context["problem"]:
            # Have both, move to understanding
            session_state.state = ConversationState.UNDERSTANDING_PROBLEM
            return {
                "success": True,
                "message": f"समझा। आपकी {session_state.context['crop']} में {session_state.context['problem']} की समस्या है। ये कब से है?",
                "state": session_state.state,
                "next_expected": "duration_or_severity"
            }
        
        elif session_state.context["crop"]:
            return {
                "success": True,
                "message": f"{session_state.context['crop']} की फसल में क्या समस्या है? जैसे - कीट, रोग, पोषण की कमी, आदि।",
                "state": session_state.state,
                "next_expected": "problem_description"
            }
        
        else:
            return {
                "success": True,
                "message": "कृपया पहले बताएं कि आप किस फसल के बारे में पूछना चाहते हैं?",
                "state": session_state.state,
                "next_expected": "crop_name"
            }
    
    async def _handle_understanding_problem(
        self,
        session_state: ConversationState,
        message: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Understand problem details before providing solution"""
        
        # Validate that farmer provided some details
        if len(message.strip()) < 10:
            return {
                "success": True,
                "message": "कृपया अपनी समस्या के बारे में थोड़ा विस्तार से बताएं। जैसे - कब से समस्या है? कितना नुकसान हुआ है? पूरे खेत में है या कुछ हिस्से में?",
                "state": session_state.state,
                "retry": True,
                "suggestions": ["1-2 दिन से", "1 हफ्ते से", "बहुत ज्यादा", "थोड़ा सा"]
            }
        
        # Collect severity/duration info
        session_state.context["severity"] = message  # Store additional details
        
        # Move to providing solution
        session_state.state = ConversationState.PROVIDING_SOLUTION
        return {
            "success": True,
            "message": "ठीक है, मैं आपके लिए सबसे अच्छा समाधान ढूंढ रहा हूं...",
            "state": session_state.state,
            "context": session_state.context
        }
    
    async def _handle_providing_solution(
        self,
        session_state: ConversationState,
        message: str,
        entities: Dict[str, Any],
        call_session_id: int
    ) -> Dict[str, Any]:
        """Generate solution using RAG + LLM"""
        
        # Build query for RAG
        query = self._build_rag_query(session_state.context, message)
        
        # Get solution from advisory service
        try:
            result = await self.advisory_service.generate_advisory(
                farmer_query=query,
                session_id=str(call_session_id)
            )
            
            advisory_text = result.get("advisory_text", "")
            confidence = result.get("confidence", 0.0)
            
            session_state.state = ConversationState.FOLLOWUP
            
            return {
                "success": True,
                "message": advisory_text,
                "state": session_state.state,
                "confidence": confidence,
                "context": session_state.context,
                "next_expected": "followup_or_new_query",
                "suggestions": ["क्या कोई और दवा है?", "कितनी मात्रा में डालूं?", "नया सवाल पूछना है"]
            }
            
        except Exception as e:
            logger.error(f"Error generating solution: {e}")
            return {
                "success": False,
                "message": "क्षमा करें, अभी समाधान नहीं मिल पा रहा है। कृपया हमारे विशेषज्ञ से बात करें।",
                "state": session_state.state,
                "error": str(e)
            }
    
    async def _handle_followup(
        self,
        session_state: ConversationState,
        message: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle followup questions"""
        
        # Check if it's a new query or followup
        if any(word in message.lower() for word in ["नया", "दूसरा", "और", "अलग"]):
            # Reset for new query
            session_state.state = ConversationState.INITIAL
            session_state.context["crop"] = None
            session_state.context["problem"] = None
            return {
                "success": True,
                "message": "ठीक है, आप किस फसल के बारे में जानना चाहते हैं?",
                "state": session_state.state,
                "next_expected": "crop_name"
            }
        
        else:
            # It's a followup question
            session_state.state = ConversationState.PROVIDING_SOLUTION
            return {
                "success": True,
                "message": "मैं आपके सवाल का जवाब ढूंढ रहा हूं...",
                "state": session_state.state
            }
    
    def _build_rag_query(self, context: Dict[str, Any], current_message: str) -> str:
        """Build optimized query for RAG retrieval"""
        crop = context.get("crop", "")
        problem = context.get("problem", "")
        
        if crop and problem:
            return f"{crop} में {problem} की समस्या का समाधान। {current_message}"
        elif crop:
            return f"{crop} की खेती के बारे में। {current_message}"
        else:
            return current_message
    
    def _generate_greeting(self, organisation_name: str = None) -> str:
        """Generate personalized greeting"""
        if organisation_name:
            return f"नमस्ते! मैं {organisation_name} का AI सहायक हूं। मैं आपकी खेती से जुड़ी समस्याओं में मदद कर सकता हूं। आप किस बारे में पूछना चाहते हैं?"
        else:
            return "नमस्ते! मैं आपकी खेती से जुड़ी समस्याओं में मदद कर सकता हूं। आप किस बारे में पूछना चाहते हैं?"
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get full conversation history"""
        session_state = self.sessions.get(session_id)
        if session_state:
            return session_state.context["history"]
        return []
    
    def clear_session(self, session_id: str):
        """Clear conversation session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def _get_state_suggestions(self, state: str) -> list:
        """Get helpful suggestions based on current state"""
        suggestions = {
            ConversationState.INITIAL: [
                "मेरी फसल में कीड़े लग गए हैं",
                "पौधे की पत्तियां सूख रही हैं",
                "फसल में बीमारी है"
            ],
            ConversationState.GATHERING_INFO: [
                "धान की फसल",
                "गेहूं की खेती",
                "टमाटर की फसल",
                "कपास"
            ],
            ConversationState.UNDERSTANDING_PROBLEM: [
                "बहुत ज्यादा नुकसान हो रहा है",
                "थोड़ा सा प्रभावित है",
                "पूरे खेत में फैल गया है"
            ],
            ConversationState.FOLLOWUP: [
                "और कुछ बताइए",
                "कितनी मात्रा में दवा डालें?",
                "कब छिड़काव करें?"
            ]
        }
        return suggestions.get(state, ["हां", "नहीं", "और बताइए"])


# Global instance
conversation_manager = ConversationManager()
