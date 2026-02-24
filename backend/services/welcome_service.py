"""
Welcome Service for AI Voice System
Generates welcome messages and audio for incoming calls
"""

import os
import logging
from datetime import datetime
from typing import Tuple, Optional
from voice.providers.google_tts import GoogleTTSProvider

logger = logging.getLogger(__name__)


class WelcomeService:
    """Handles welcome message generation and audio synthesis"""
    
    def __init__(self):
        self.tts = GoogleTTSProvider()
        self.audio_dir = "/tmp/audio"
        os.makedirs(self.audio_dir, exist_ok=True)
    
    def generate_welcome_message(self, org_name: Optional[str] = None) -> str:
        """
        Generate welcome message in Hindi
        
        Args:
            org_name: Organisation name (optional)
        
        Returns:
            Welcome message text in Hindi
        """
        if org_name:
            message = f"""नमस्ते! मैं किसान वाणी हूं, आपकी कृषि सहायक।

मैं आपकी खेती से जुड़ी किसी भी समस्या में मदद कर सकती हूं।



कृपया अपनी समस्या बताएं।"""
        else:
            message = """नमस्ते! मैं किसान वाणी हूं, आपकी कृषि सहायक।

मैं आपकी खेती से जुड़ी किसी भी समस्या में मदद कर सकती हूं।

कृपया अपनी समस्या बताएं।"""
        
        return message.strip()
    
    async def create_welcome_audio(
        self, 
        org_name: Optional[str] = None,
        session_id: Optional[int] = None
    ) -> Tuple[bytes, str]:
        """
        Create welcome audio file using Google TTS
        
        Args:
            org_name: Organisation name
            session_id: Call session ID for filename
        
        Returns:
            Tuple of (audio_bytes, filename)
        """
        try:
            # Generate message
            message = self.generate_welcome_message(org_name)
            logger.info(f"Generated welcome message: {message[:50]}...")
            
            # Synthesize to audio
            audio_bytes = await self.tts.synthesize(message, language='hi')
            logger.info(f"Synthesized audio: {len(audio_bytes)} bytes")
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_part = f"_{session_id}" if session_id else ""
            filename = f"welcome{session_part}_{timestamp}.wav"
            
            # Save audio file
            filepath = os.path.join(self.audio_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(audio_bytes)
            
            logger.info(f"✅ Welcome audio saved: {filepath}")
            
            return audio_bytes, filename
        
        except Exception as e:
            logger.error(f"❌ Error creating welcome audio: {e}")
            raise
    
    def generate_consent_message(self) -> str:
        """Generate consent/privacy message"""
        return """कृपया ध्यान दें, यह कॉल रिकॉर्ड की जा सकती है और आपकी बेहतर सेवा के लिए उपयोग की जाएगी।

क्या आप आगे बढ़ना चाहते हैं? कृपया हाँ या ना में उत्तर दें।"""
    
    def generate_question_prompt(self, question_type: str = "general") -> str:
        """
        Generate prompts for asking specific questions
        
        Args:
            question_type: Type of question to ask
        
        Returns:
            Question prompt in Hindi
        """
        prompts = {
            # Basic Information
            "name": "कृपया अपना नाम बताएं।",
            "location": "आप कहाँ से बोल रहे हैं? कृपया अपने गाँव या शहर का नाम बताएं।",
            
            # Farming Area Information
            "total_area": "आपके पास कुल कितनी खेती है? कृपया एकड़ या बीघा में बताएं।",
            "total_area_confirm": "ठीक है, तो आपके पास कुल {area} खेती है। सही है ना?",
            
            # Crop Information
            "crop": "आप किस फसल के बारे में पूछना चाहते हैं?",
            "crop_list": "अच्छा। आप कौन-कौन सी फसलें उगाते हैं? एक-एक करके बताएं।",
            "which_crop_problem": "किस फसल में समस्या आ रही है?",
            
            # Crop Area Details
            "crop_area": "इस {crop} की खेती आपने कितने एकड़ या बीघा में की है?",
            "crop_area_confirm": "समझा, तो {crop} {area} में लगाया है। सही है?",
            
            # Problem Area Details
            "affected_area": "इस {crop} के कुल {total_area} में से कितने हिस्से में समस्या है?",
            "affected_percentage": "क्या पूरी फसल प्रभावित है या कुछ हिस्से में? प्रतिशत में बताएं या कहें पूरी फसल।",
            "affected_severity": "समस्या कितनी गंभीर है? थोड़ी, मध्यम, या बहुत ज्यादा?",
            
            # Problem Details
            "problem": "कृपया अपनी समस्या विस्तार से बताएं। क्या दिख रहा है फसल में?",
            "problem_duration": "यह समस्या कब से है? कितने दिन या हफ्ते हुए?",
            "problem_symptoms": "और क्या लक्षण दिख रहे हैं? जैसे पत्तियों का रंग, धब्बे, कीड़े वगैरह?",
            
            # Previous Actions
            "previous_treatment": "क्या आपने इसके लिए कुछ उपाय या दवा पहले से की है?",
            "previous_treatment_result": "उससे क्या फर्क पड़ा? सुधार हुआ या नहीं?",
            
            # Environmental Context
            "weather": "पिछले कुछ दिनों में मौसम कैसा रहा? बारिश, धूप, या कुछ खास?",
            "irrigation": "पानी की व्यवस्था कैसी है? नियमित सिंचाई हो रही है?",
            "soil_type": "आपकी मिट्टी किस प्रकार की है? काली, लाल, चिकनी, या रेतीली?",
            
            # General
            "general": "मैं आपकी कैसे मदद कर सकती हूं?",
            "clarify": "मैं सही से समझ नहीं पाई। कृपया फिर से बताएं।",
            "continue": "क्या आप कुछ और पूछना चाहेंगे?",
            "more_details": "कुछ और विवरण देना चाहेंगे?",
            
            # Closing
            "goodbye": "धन्यवाद! आपकी समस्या का समाधान जल्द मिलेगा। खेती के लिए शुभकामनाएं। किसी भी समस्या के लिए फिर से संपर्क करें। नमस्ते!",
            "goodbye_short": "धन्यवाद! नमस्ते!"
        }
        
        return prompts.get(question_type, prompts["general"])
    
    async def create_question_audio(
        self, 
        question_type: str,
        session_id: Optional[int] = None
    ) -> Tuple[bytes, str]:
        """
        Create audio for asking questions
        
        Args:
            question_type: Type of question
            session_id: Call session ID
        
        Returns:
            Tuple of (audio_bytes, filename)
        """
        try:
            # Generate question
            question = self.generate_question_prompt(question_type)
            
            # Synthesize to audio
            audio_bytes = await self.tts.synthesize(question, language='hi')
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_part = f"_{session_id}" if session_id else ""
            filename = f"{question_type}{session_part}_{timestamp}.wav"
            
            # Save audio file
            filepath = os.path.join(self.audio_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(audio_bytes)
            
            logger.info(f"✅ Question audio saved: {filepath}")
            
            return audio_bytes, filename
        
        except Exception as e:
            logger.error(f"❌ Error creating question audio: {e}")
            raise


# Global instance
welcome_service = WelcomeService()


class ConversationFlow:
    """
    Manages the conversation flow for gathering farming information
    Defines the sequence of questions to ask
    """
    
    # Standard conversation flow
    FLOW_SEQUENCE = [
        "name",              # 1. किसान का नाम
        "location",          # 2. गाँव/शहर
        "total_area",        # 3. कुल खेती का क्षेत्रफल
        "which_crop_problem",# 4. किस फसल में समस्या है
        "crop_area",         # 5. उस फसल का क्षेत्रफल
        "affected_area",     # 6. कितने हिस्से में समस्या
        "problem",           # 7. समस्या का विवरण
        "problem_duration",  # 8. कब से है समस्या
        "problem_symptoms",  # 9. और क्या लक्षण
        "previous_treatment",# 10. पहले क्या किया
        "weather",           # 11. मौसम की जानकारी
        "irrigation",        # 12. सिंचाई की व्यवस्था
    ]
    
    @classmethod
    def get_next_question(cls, current_step: int) -> tuple[str, str]:
        """
        Get next question in the flow
        
        Args:
            current_step: Current step number (0-indexed)
        
        Returns:
            Tuple of (question_type, question_text)
        """
        if current_step >= len(cls.FLOW_SEQUENCE):
            return "complete", "सभी जानकारी मिल गई है। धन्यवाद!"
        
        question_type = cls.FLOW_SEQUENCE[current_step]
        question_text = welcome_service.generate_question_prompt(question_type)
        
        return question_type, question_text
    
    @classmethod
    def get_question_with_context(cls, question_type: str, context: dict) -> str:
        """
        Get question with dynamic context (e.g., crop name, area)
        
        Args:
            question_type: Type of question
            context: Dictionary with values like crop, area, etc.
        
        Returns:
            Formatted question string
        """
        question_template = welcome_service.generate_question_prompt(question_type)
        
        # Replace placeholders with actual values
        if "{crop}" in question_template and "crop" in context:
            question_template = question_template.replace("{crop}", context["crop"])
        
        if "{area}" in question_template and "area" in context:
            question_template = question_template.replace("{area}", context["area"])
        
        if "{total_area}" in question_template and "total_area" in context:
            question_template = question_template.replace("{total_area}", context["total_area"])
        
        return question_template
    
    @classmethod
    def get_progress(cls, current_step: int) -> dict:
        """
        Get conversation progress
        
        Returns:
            Dictionary with progress information
        """
        total_steps = len(cls.FLOW_SEQUENCE)
        percentage = min(100, int((current_step / total_steps) * 100))
        
        return {
            "current_step": current_step,
            "total_steps": total_steps,
            "percentage": percentage,
            "completed": current_step >= total_steps,
            "questions_asked": current_step,
            "questions_remaining": max(0, total_steps - current_step)
        }


# Global instances
conversation_flow = ConversationFlow()
