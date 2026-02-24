"""
Multi-Turn Dialogue Management Service
Manages conversation state and multi-turn interactions
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DialogueState(str, Enum):
    """States in the conversation flow"""
    PROFILE_COLLECTION = "profile_collection"
    GREETING = "greeting"
    PROBLEM_IDENTIFICATION = "problem_identification"
    DETAIL_GATHERING = "detail_gathering"
    SOLUTION_PROVIDING = "solution_providing"
    CLARIFICATION = "clarification"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"
    ENDED = "ended"


class DialogueManager:
    """Manages multi-turn conversation state and transitions"""
    
    def __init__(self):
        # State transition rules
        self.state_transitions = {
            DialogueState.PROFILE_COLLECTION: [
                DialogueState.GREETING
            ],
            DialogueState.GREETING: [
                DialogueState.PROBLEM_IDENTIFICATION,
                DialogueState.CLOSING
            ],
            DialogueState.PROBLEM_IDENTIFICATION: [
                DialogueState.DETAIL_GATHERING,
                DialogueState.CLARIFICATION,
                DialogueState.SOLUTION_PROVIDING
            ],
            DialogueState.DETAIL_GATHERING: [
                DialogueState.DETAIL_GATHERING,  # More details needed
                DialogueState.SOLUTION_PROVIDING,
                DialogueState.CLARIFICATION
            ],
            DialogueState.SOLUTION_PROVIDING: [
                DialogueState.FOLLOW_UP,
                DialogueState.CLOSING,
                DialogueState.CLARIFICATION
            ],
            DialogueState.FOLLOW_UP: [
                DialogueState.PROBLEM_IDENTIFICATION,  # New problem
                DialogueState.CLOSING
            ],
            DialogueState.CLARIFICATION: [
                DialogueState.PROBLEM_IDENTIFICATION,
                DialogueState.DETAIL_GATHERING,
                DialogueState.SOLUTION_PROVIDING
            ],
            DialogueState.CLOSING: [
                DialogueState.ENDED
            ]
        }
        
        # Required information for each problem type
        self.required_info = {
            "pest_problem": ["crop", "pest_description", "affected_area", "duration"],
            "disease_problem": ["crop", "symptoms", "affected_plants", "weather"],
            "nutrient_problem": ["crop", "symptoms", "last_fertilizer", "soil_type"],
            "crop_advice": ["crop", "land_area", "season", "irrigation"]
        }
    
    def initialize_dialogue(self, call_session_id: int) -> Dict[str, Any]:
        """Initialize a new dialogue session"""
        return {
            "call_session_id": call_session_id,
            "current_state": DialogueState.PROFILE_COLLECTION,
            "intent": None,
            "entities": {},
            "missing_info": ["name", "crop", "land_size"],
            "conversation_history": [],
            "turn_count": 0,
            "started_at": datetime.utcnow().isoformat(),
            "metadata": {}
        }
    
    async def update_dialogue_state(
        self,
        dialogue_context: Dict[str, Any],
        user_input: str,
        intent: str,
        entities: Dict[str, Any],
        ai_response: str,
        db=None
    ) -> Dict[str, Any]:
        """
        Update dialogue state based on user input and AI response
        
        Args:
            dialogue_context: Current dialogue context
            user_input: User's transcribed input
            intent: Detected intent
            entities: Extracted entities
            ai_response: AI's response
            db: Optional database session for call status check
            
        Returns:
            Updated dialogue context with new state
        """
        # AI SAFETY GUARD: Check call status before processing
        call_session_id = dialogue_context.get("call_session_id")
        if db and call_session_id:
            from services.call_session_service import CallSessionService
            call_service = CallSessionService(db)
            call_session = await call_service.get_call_session(call_session_id)
            if call_session and str(call_session.status).lower() != "active":
                logger.warning(f"AI processing stopped: Call session {call_session_id} status is {call_session.status}")
                dialogue_context["ai_processing_stopped"] = True
                return dialogue_context

        current_state = dialogue_context["current_state"]

        # Add to conversation history
        dialogue_context["conversation_history"].append({
            "turn": dialogue_context["turn_count"] + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": user_input,
            "intent": intent,
            "entities": entities,
            "ai_response": ai_response,
            "state": current_state
        })

        dialogue_context["turn_count"] += 1

        # Update entities
        dialogue_context["entities"].update(entities)

        # Update intent if primary problem identified
        if not dialogue_context["intent"] and intent not in ["greeting", "yes", "no", "unclear"]:
            dialogue_context["intent"] = intent

        # Determine next state
        next_state = self._determine_next_state(
            current_state,
            intent,
            dialogue_context["entities"],
            dialogue_context.get("intent")
        )

        dialogue_context["current_state"] = next_state

        # Update missing information
        if dialogue_context.get("intent"):
            dialogue_context["missing_info"] = self._get_missing_info(
                dialogue_context["intent"],
                dialogue_context["entities"]
            )

        return dialogue_context
    
    def _determine_next_state(
        self,
        current_state: str,
        intent: str,
        entities: Dict[str, Any],
        problem_intent: Optional[str]
    ) -> str:
        """Determine next dialogue state"""
        
        # From GREETING
        if current_state == DialogueState.GREETING:
            if intent in ["pest_problem", "disease_problem", "nutrient_problem", "crop_advice"]:
                return DialogueState.PROBLEM_IDENTIFICATION
            elif intent in ["thanks", "no"]:
                return DialogueState.CLOSING
            return DialogueState.PROBLEM_IDENTIFICATION
        
        # From PROBLEM_IDENTIFICATION
        elif current_state == DialogueState.PROBLEM_IDENTIFICATION:
            if problem_intent:
                missing_info = self._get_missing_info(problem_intent, entities)
                if missing_info:
                    return DialogueState.DETAIL_GATHERING
                else:
                    return DialogueState.SOLUTION_PROVIDING
            elif intent == "unclear":
                return DialogueState.CLARIFICATION
            return DialogueState.DETAIL_GATHERING
        
        # From DETAIL_GATHERING
        elif current_state == DialogueState.DETAIL_GATHERING:
            if problem_intent:
                missing_info = self._get_missing_info(problem_intent, entities)
                if not missing_info:
                    return DialogueState.SOLUTION_PROVIDING
            return DialogueState.DETAIL_GATHERING
        
        # From SOLUTION_PROVIDING
        elif current_state == DialogueState.SOLUTION_PROVIDING:
            if intent in ["thanks", "yes"]:
                return DialogueState.FOLLOW_UP
            elif intent == "no":
                return DialogueState.CLARIFICATION
            return DialogueState.FOLLOW_UP
        
        # From FOLLOW_UP
        elif current_state == DialogueState.FOLLOW_UP:
            if intent in ["pest_problem", "disease_problem", "nutrient_problem", "crop_advice"]:
                return DialogueState.PROBLEM_IDENTIFICATION
            elif intent in ["thanks", "no"]:
                return DialogueState.CLOSING
            return DialogueState.CLOSING
        
        # From CLARIFICATION
        elif current_state == DialogueState.CLARIFICATION:
            if intent in ["pest_problem", "disease_problem", "nutrient_problem", "crop_advice"]:
                return DialogueState.PROBLEM_IDENTIFICATION
            return DialogueState.DETAIL_GATHERING
        
        # From CLOSING
        elif current_state == DialogueState.CLOSING:
            return DialogueState.ENDED
        
        return current_state
    
    def _get_missing_info(self, intent: str, entities: Dict[str, Any]) -> List[str]:
        """Get list of missing required information"""
        required = self.required_info.get(intent, [])
        missing = []
        
        for info in required:
            if info not in entities or not entities[info]:
                missing.append(info)
        
        return missing
    
    def get_next_prompt(self, dialogue_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate next prompt based on dialogue state
        
        Returns:
            {
                "prompt_type": str,
                "prompt_text": str,
                "expected_info": List[str]
            }
        """
        state = dialogue_context["current_state"]
        missing_info = dialogue_context.get("missing_info", [])
        intent = dialogue_context.get("intent")
        
        # State-specific prompts
        if state == DialogueState.PROFILE_COLLECTION:
            missing_info = dialogue_context.get("missing_info", [])
            if missing_info:
                info = missing_info[0]
                prompts = {
                    "name": "कृपया अपना नाम बताएं।",
                    "crop": "आप कौन सी फसल उगा रहे हैं?",
                    "land_size": "आपके पास कितनी जमीन है (एकड़ में)?"
                }
                return {
                    "prompt_type": "profile_question",
                    "prompt_text": prompts.get(info, f"{info} बताएं।"),
                    "expected_info": [info]
                }
            else:
                return {
                    "prompt_type": "profile_complete",
                    "prompt_text": "धन्यवाद! अब आप अपनी खेती से जुड़ा सवाल पूछ सकते हैं।",
                    "expected_info": []
                }
        if state == DialogueState.GREETING:
            return {
                "prompt_type": "greeting",
                "prompt_text": "नमस्ते! मैं किसान AI हूं। मैं आपकी खेती से जुड़ी समस्या में मदद कर सकती हूं। बताइए, क्या समस्या है?",
                "expected_info": ["problem_description"]
            }
        
        elif state == DialogueState.PROBLEM_IDENTIFICATION:
            return {
                "prompt_type": "problem_inquiry",
                "prompt_text": "कृपया अपनी समस्या विस्तार से बताएं। कौन सी फसल है और क्या दिक्कत हो रही है?",
                "expected_info": ["crop", "problem_type"]
            }
        
        elif state == DialogueState.DETAIL_GATHERING:
            if missing_info:
                # Ask for first missing piece of information
                missing = missing_info[0]
                prompt_text = self._get_info_prompt(missing, intent)
                return {
                    "prompt_type": "detail_inquiry",
                    "prompt_text": prompt_text,
                    "expected_info": [missing]
                }
            return {
                "prompt_type": "detail_inquiry",
                "prompt_text": "और कुछ जानकारी बताएं जो मदद कर सके।",
                "expected_info": []
            }
        
        elif state == DialogueState.FOLLOW_UP:
            return {
                "prompt_type": "follow_up",
                "prompt_text": "क्या और कोई समस्या है जिसमें मदद कर सकूं?",
                "expected_info": ["has_more_problems"]
            }
        
        elif state == DialogueState.CLARIFICATION:
            return {
                "prompt_type": "clarification",
                "prompt_text": "मुझे ठीक से समझ नहीं आया। कृपया फिर से बताएं?",
                "expected_info": ["clarified_input"]
            }
        
        elif state == DialogueState.CLOSING:
            return {
                "prompt_type": "closing",
                "prompt_text": "धन्यवाद! आपको और मदद चाहिए तो फिर से कॉल करें। फसल अच्छी हो!",
                "expected_info": []
            }
        
        return {
            "prompt_type": "generic",
            "prompt_text": "कृपया बताएं।",
            "expected_info": []
        }
    
    def _get_info_prompt(self, info_type: str, intent: Optional[str]) -> str:
        """Get prompt for specific information type"""
        prompts = {
            "crop": "आप कौन सी फसल उगा रहे हैं?",
            "pest_description": "कीट कैसा दिख रहा है? रंग और आकार बताएं।",
            "affected_area": "कितना क्षेत्र प्रभावित है?",
            "duration": "यह समस्या कब से है?",
            "symptoms": "पौधे में क्या-क्या लक्षण दिख रहे हैं?",
            "affected_plants": "कितने पौधे प्रभावित हैं?",
            "weather": "पिछले दिनों मौसम कैसा रहा?",
            "last_fertilizer": "आखिरी बार कौन सी खाद डाली थी?",
            "soil_type": "आपकी मिट्टी कैसी है - काली, लाल या दोमट?",
            "land_area": "आपके पास कितनी जमीन है?",
            "season": "कौन सी सीजन में बोना चाहते हैं?",
            "irrigation": "सिंचाई की सुविधा है?"
        }
        
        return prompts.get(info_type, f"{info_type} के बारे में बताएं।")
    
    def should_end_conversation(self, dialogue_context: Dict[str, Any]) -> bool:
        """Check if conversation should end"""
        return (
            dialogue_context["current_state"] == DialogueState.ENDED or
            dialogue_context["turn_count"] >= 15 or  # Max 15 turns
            (dialogue_context["current_state"] == DialogueState.CLOSING and
             dialogue_context["turn_count"] > 0)
        )


# Global instance
dialogue_manager = DialogueManager()
