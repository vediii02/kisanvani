from openai import AsyncOpenAI
from core.config import settings
from rag.prompt_templates import create_advisory_prompt, ADVISORY_SYSTEM_MESSAGE
from rag.gemini_retriever import GeminiRAGRetriever
from rag.confidence import calculate_confidence, should_escalate
import logging

logger = logging.getLogger(__name__)

class AdvisoryService:
    def __init__(self):
        self.rag = None
        self.client = AsyncOpenAI(api_key=settings.EMERGENT_LLM_KEY)
    
    def _get_rag(self):
        if self.rag is None:
            self.rag = GeminiRAGRetriever(settings.QDRANT_URL, settings.QDRANT_COLLECTION)
        return self.rag
    
    async def generate_advisory(self, farmer_query: str, session_id: str) -> dict:
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
        
        context_docs = [hit['metadata'] for hit in search_results]
        prompt = create_advisory_prompt(farmer_query, context_docs)
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.DEFAULT_LLM_MODEL,
                messages=[
                    {"role": "system", "content": ADVISORY_SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            advisory_text = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            advisory_text = "क्षमा करें, अभी हम आपकी मदद नहीं कर पा रहे हैं। कृपया बाद में फिर से प्रयास करें।"
        
        return {
            'advisory_text': advisory_text,
            'confidence': confidence,
            'escalated': False,
            'kb_entries': [hit['id'] for hit in search_results],
            'reason': None
        }

advisory_service = AdvisoryService()
