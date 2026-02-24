"""
RAG AI Response Generation Service
Generates contextual responses using retrieval-augmented generation
"""

import logging
import os
from typing import Dict, Any, List, Optional
import httpx
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class RAGResponseService:
    """Generate AI responses using RAG pipeline"""
    
    def __init__(self):
        self.openai_client = None
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.use_mock = os.getenv("USE_MOCK_AI", "false").lower() == "true"
        
        if self.openai_api_key and not self.use_mock:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
    
    async def generate_response(
        self,
        query: str,
        intent: str,
        entities: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate contextual response using RAG
        
        Args:
            query: Farmer's question/input
            intent: Detected intent
            entities: Extracted entities (crop, pest, etc.)
            context: Conversation context
            retrieved_docs: Retrieved knowledge base documents
            
        Returns:
            {
                "success": bool,
                "response": str (Hindi response),
                "confidence": float,
                "sources": List[str],
                "follow_up_questions": List[str],
                "error": Optional[str]
            }
        """
        try:
            if self.use_mock or not self.openai_client:
                return await self._generate_mock_response(query, intent, entities)
            
            # Build context from retrieved documents
            knowledge_context = self._build_knowledge_context(retrieved_docs)
            
            # Build conversation history
            conversation_history = self._build_conversation_history(context)
            
            # Create system prompt
            system_prompt = self._create_system_prompt(intent, entities)
            
            # Create user prompt
            user_prompt = self._create_user_prompt(
                query,
                knowledge_context,
                conversation_history,
                entities
            )
            
            # Generate response
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Extract follow-up questions
            follow_ups = self._extract_follow_up_questions(ai_response, intent)
            
            # Extract sources
            sources = self._extract_sources(retrieved_docs)
            
            return {
                "success": True,
                "response": ai_response,
                "confidence": 0.9,
                "sources": sources,
                "follow_up_questions": follow_ups,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"RAG response generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "response": "माफ़ कीजिए, मुझे आपकी समस्या को समझने में दिक्कत हो रही है। कृपया फिर से बताएं।",
                "confidence": 0.0,
                "sources": [],
                "follow_up_questions": [],
                "error": str(e)
            }
    
    def _create_system_prompt(self, intent: str, entities: Dict[str, Any]) -> str:
        """Create system prompt based on intent and entities"""
        base_prompt = """तुम एक अनुभवी कृषि सलाहकार हो जो भारतीय किसानों की मदद करता है। 
तुम्हारा काम है:
1. किसानों की समस्याओं को समझना
2. व्यावहारिक और सटीक सलाह देना
3. स्थानीय संदर्भ में जवाब देना
4. हिंदी में स्पष्ट और सरल भाषा में बात करना

महत्वपूर्ण:
- जवाब 2-3 वाक्यों में दो, बहुत लंबा नहीं
- तकनीकी शब्दों को सरल भाषा में समझाओ
- अगर जानकारी नहीं है तो स्पष्ट रूप से बताओ
- खतरनाक या गलत सलाह कभी मत दो
"""
        
        # Intent-specific additions
        if intent == "pest_problem":
            base_prompt += "\n\nतुम कीट समस्याओं के विशेषज्ञ हो। पहले कीट की पहचान करो, फिर उपाय बताओ।"
        elif intent == "disease_problem":
            base_prompt += "\n\nतुम फसल रोगों के विशेषज्ञ हो। रोग के लक्षण और उपचार बताओ।"
        elif intent == "nutrient_problem":
            base_prompt += "\n\nतुम मृदा और पोषण के विशेषज्ञ हो। खाद और उर्वरक की सलाह दो।"
        elif intent == "crop_advice":
            base_prompt += "\n\nतुम फसल उत्पादन के विशेषज्ञ हो। बुवाई से कटाई तक की सलाह दो।"
        
        # Add entity context
        if entities.get("crop"):
            base_prompt += f"\n\nफसल: {entities['crop']}"
        
        return base_prompt
    
    def _create_user_prompt(
        self,
        query: str,
        knowledge_context: str,
        conversation_history: str,
        entities: Dict[str, Any]
    ) -> str:
        """Create user prompt with context"""
        prompt = f"किसान का सवाल: {query}\n\n"
        
        if knowledge_context:
            prompt += f"ज्ञान आधार से जानकारी:\n{knowledge_context}\n\n"
        
        if conversation_history:
            prompt += f"पिछली बातचीत:\n{conversation_history}\n\n"
        
        if entities:
            prompt += f"महत्वपूर्ण जानकारी: {entities}\n\n"
        
        prompt += "कृपया किसान को हिंदी में संक्षिप्त और स्पष्ट जवाब दें।"
        
        return prompt
    
    def _build_knowledge_context(self, retrieved_docs: Optional[List[Dict[str, Any]]]) -> str:
        """Build context from retrieved documents"""
        if not retrieved_docs:
            return ""
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs[:3], 1):  # Top 3 documents
            content = doc.get("content", "")
            score = doc.get("score", 0.0)
            if content and score > 0.7:
                context_parts.append(f"{i}. {content}")
        
        return "\n".join(context_parts)
    
    def _build_conversation_history(self, context: Optional[Dict[str, Any]]) -> str:
        """Build conversation history from context"""
        if not context or "history" not in context:
            return ""
        
        history = context["history"]
        history_parts = []
        
        for turn in history[-3:]:  # Last 3 turns
            if turn.get("question"):
                history_parts.append(f"प्रश्न: {turn['question']}")
            if turn.get("answer"):
                history_parts.append(f"जवाब: {turn['answer']}")
        
        return "\n".join(history_parts)
    
    def _extract_follow_up_questions(self, response: str, intent: str) -> List[str]:
        """Extract or generate follow-up questions"""
        follow_ups = []
        
        if intent == "pest_problem":
            follow_ups = [
                "कीट कब से दिख रहे हैं?",
                "पौधे के किस हिस्से पर ज्यादा हैं?",
                "क्या कोई दवा पहले डाली थी?"
            ]
        elif intent == "disease_problem":
            follow_ups = [
                "पत्तियों पर कैसे धब्बे हैं?",
                "कितने पौधे प्रभावित हैं?",
                "मौसम कैसा रहा है?"
            ]
        elif intent == "crop_advice":
            follow_ups = [
                "आपके पास कितनी जमीन है?",
                "पिछली फसल क्या थी?",
                "सिंचाई की सुविधा है?"
            ]
        
        return follow_ups[:2]  # Return top 2
    
    def _extract_sources(self, retrieved_docs: Optional[List[Dict[str, Any]]]) -> List[str]:
        """Extract source information from documents"""
        if not retrieved_docs:
            return []
        
        sources = []
        for doc in retrieved_docs[:2]:  # Top 2 sources
            if doc.get("metadata", {}).get("source"):
                sources.append(doc["metadata"]["source"])
        
        return sources
    
    async def _generate_mock_response(
        self,
        query: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate mock response for testing"""
        crop = entities.get("crop", "फसल")
        
        mock_responses = {
            "pest_problem": f"आपकी {crop} में कीट की समस्या है। तुरंत कीटनाशक का छिड़काव करें। नीम का तेल या इमिडाक्लोप्रिड का इस्तेमाल कर सकते हैं। 7-10 दिन में सुधार दिखेगा।",
            "disease_problem": f"यह {crop} में फंगल रोग लग रहा है। कार्बेन्डाज़िम या मैंकोजेब का स्प्रे करें। प्रभावित पत्तियां हटा दें।",
            "nutrient_problem": f"{crop} में पोषण की कमी दिख रही है। NPK 19:19:19 खाद डालें। मिट्टी की जांच भी करवाएं।",
            "crop_advice": f"{crop} की खेती के लिए अच्छी जल निकासी वाली मिट्टी चाहिए। बुवाई का सही समय है। बीज उपचार जरूर करें।",
            "product_info": "हमारे पास कई अच्छे उत्पाद हैं। आपकी समस्या के अनुसार सुझाव दे सकते हैं।"
        }
        
        response = mock_responses.get(intent, "कृपया अपनी समस्या विस्तार से बताएं।")
        
        return {
            "success": True,
            "response": response,
            "confidence": 0.85,
            "sources": ["किसान ज्ञान आधार"],
            "follow_up_questions": ["और कुछ जानना चाहते हैं?"],
            "error": None
        }


# Global instance
rag_service = RAGResponseService()
