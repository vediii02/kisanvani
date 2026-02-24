"""
Production Advisory Service using Gemini AI
"""

import google.generativeai as genai
from core.config import settings
from rag.prompt_templates import create_advisory_prompt, ADVISORY_SYSTEM_MESSAGE
from rag.gemini_retriever import GeminiRAGRetriever
from rag.confidence import calculate_confidence, should_escalate
import logging
import os

logger = logging.getLogger(__name__)


class GeminiAdvisoryService:
    """Production-ready advisory service with Gemini"""
    
    def __init__(self):
        self.rag = None
        self.enabled = False
        # Configure Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            logger.warning("⚠️ GEMINI_API_KEY not found - Gemini service disabled")
            return
        try:
            genai.configure(api_key=gemini_key)
            self.enabled = True
            logger.info("✅ Gemini Advisory Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.enabled = False
    
    def _get_rag(self):
        if self.rag is None:
            self.rag = GeminiRAGRetriever(settings.QDRANT_URL, settings.QDRANT_COLLECTION)
        return self.rag
    
    async def generate_advisory(self, farmer_query: str, session_id: str) -> dict:
        """Generate advisory using Gemini + RAG"""
        
        if not self.enabled:
            return {
                'advisory_text': 'सेवा अस्थायी रूप से अनुपलब्ध है। कृपया बाद में प्रयास करें।',
                'confidence': 0.0,
                'escalated': True,
                'kb_entries': [],
                'reason': 'Gemini service not configured'
            }
        
        try:
            rag = self._get_rag()
            search_results = rag.search(farmer_query, top_k=3, score_threshold=0.4)
            
            confidence = calculate_confidence(search_results)
            escalate = should_escalate(confidence, settings.CONFIDENCE_THRESHOLD)
            
            logger.info(f"RAG search confidence: {confidence}, escalate: {escalate}")
            
            if escalate:
                return {
                    'advisory_text': 'आपकी समस्या को हमारे विशेषज्ञ के पास भेजा जा रहा है। वे जल्द ही आपसे संपर्क करेंगे।',
                    'confidence': confidence,
                    'escalated': True,
                    'kb_entries': [],
                    'reason': 'Low confidence score'
                }
            
            # Build context from retrieved documents
            context_docs = [hit['metadata'] for hit in search_results]
            prompt = create_advisory_prompt(farmer_query, context_docs)
            
            # Use Gemini 2.0 Flash for response generation
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            full_prompt = f"""{ADVISORY_SYSTEM_MESSAGE}

{prompt}

कृपया किसान को हिंदी में विस्तृत सलाह दें।"""
            
            response = model.generate_content(full_prompt)
            advisory_text = response.text
            
            return {
                'advisory_text': advisory_text,
                'confidence': confidence,
                'escalated': False,
                'kb_entries': [hit['id'] for hit in search_results],
                'reason': None
            }
            
        except Exception as e:
            logger.error(f"Error in Gemini advisory: {str(e)}")
            return {
                'advisory_text': "क्षमा करें, अभी हम आपकी मदद नहीं कर पा रहे हैं। कृपया बाद में फिर से प्रयास करें।",
                'confidence': 0.0,
                'escalated': True,
                'kb_entries': [],
                'reason': f'Error: {str(e)}'
            }


# Global instance
gemini_advisory_service = GeminiAdvisoryService()
