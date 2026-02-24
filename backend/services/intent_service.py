"""
Advanced Intent Detection Service
Detects farmer intent from transcribed speech
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class FarmerIntent(str, Enum):
    # Problem-related
    PEST_PROBLEM = "pest_problem"
    DISEASE_PROBLEM = "disease_problem"
    NUTRIENT_PROBLEM = "nutrient_problem"
    WATER_PROBLEM = "water_problem"
    WEATHER_PROBLEM = "weather_problem"
    
    # Information-seeking
    CROP_ADVICE = "crop_advice"
    PRODUCT_INFO = "product_info"
    PRICE_INFO = "price_info"
    MARKET_INFO = "market_info"
    
    # Transactional
    ORDER_PRODUCT = "order_product"
    CHECK_ORDER = "check_order"
    COMPLAINT = "complaint"
    
    # Conversational
    GREETING = "greeting"
    THANKS = "thanks"
    YES = "yes"
    NO = "no"
    UNCLEAR = "unclear"


class IntentDetectionService:
    """Advanced intent detection with pattern matching and NLU"""
    
    def __init__(self):
        # Hindi keywords for each intent
        self.intent_keywords = {
            FarmerIntent.PEST_PROBLEM: [
                "कीट", "कीड़े", "पोका", "इल्ली", "टिड्डी", "माहू", "सुंडी",
                "pest", "insect", "bug", "worm", "caterpillar"
            ],
            FarmerIntent.DISEASE_PROBLEM: [
                "बीमारी", "रोग", "संक्रमण", "फफूंद", "जड़ सड़न", "पत्ती झुलसा",
                "disease", "infection", "fungus", "rot", "blight"
            ],
            FarmerIntent.NUTRIENT_PROBLEM: [
                "पोषण", "खाद", "उर्वरक", "पीला", "सूखा", "कमजोर",
                "nutrient", "fertilizer", "yellow", "weak", "deficiency"
            ],
            FarmerIntent.WATER_PROBLEM: [
                "पानी", "सिंचाई", "सूखा", "बाढ़", "जलभराव",
                "water", "irrigation", "drought", "flood", "waterlogging"
            ],
            FarmerIntent.WEATHER_PROBLEM: [
                "मौसम", "बारिश", "गर्मी", "ठंड", "ओलावृष्टि",
                "weather", "rain", "heat", "cold", "hail"
            ],
            FarmerIntent.CROP_ADVICE: [
                "सलाह", "जानकारी", "कैसे", "क्या करूं", "उपाय", "तरीका",
                "advice", "information", "how", "what to do", "solution", "method"
            ],
            FarmerIntent.PRODUCT_INFO: [
                "उत्पाद", "बीज", "दवा", "कीटनाशक", "कौन सा", "कीमत",
                "product", "seed", "pesticide", "which", "price"
            ],
            FarmerIntent.PRICE_INFO: [
                "कीमत", "दाम", "रेट", "मूल्य", "कितना",
                "price", "cost", "rate", "value", "how much"
            ],
            FarmerIntent.MARKET_INFO: [
                "बाजार", "मंडी", "बिक्री", "खरीदी",
                "market", "mandi", "sell", "buy"
            ],
            FarmerIntent.ORDER_PRODUCT: [
                "ऑर्डर", "मंगवाना", "चाहिए", "खरीदना",
                "order", "want", "need", "buy"
            ],
            FarmerIntent.CHECK_ORDER: [
                "ऑर्डर", "स्थिति", "कहाँ है", "मिला",
                "order", "status", "where", "received"
            ],
            FarmerIntent.COMPLAINT: [
                "शिकायत", "समस्या", "गलत", "खराब",
                "complaint", "problem", "wrong", "bad"
            ],
            FarmerIntent.GREETING: [
                "नमस्ते", "हेलो", "प्रणाम", "सुप्रभात",
                "hello", "hi", "namaste", "good morning"
            ],
            FarmerIntent.THANKS: [
                "धन्यवाद", "शुक्रिया", "थैंक्स", "अच्छा",
                "thank", "thanks", "good"
            ],
            FarmerIntent.YES: [
                "हाँ", "जी", "ठीक", "सही", "बिलकुल",
                "yes", "ok", "right", "correct", "sure"
            ],
            FarmerIntent.NO: [
                "नहीं", "ना", "मत",
                "no", "not", "don't"
            ]
        }
        
        # Context-aware patterns
        self.context_patterns = {
            "problem_description": [
                r"(में|पर|को)\s+(कीट|बीमारी|रोग|समस्या)",
                r"(लग|हो)\s+गए?\s+(हैं|है)",
                r"(पत्ती|फसल|पौधा)\s+(पीला|सूखा|मुरझा)"
            ],
            "advice_seeking": [
                r"(क्या|कैसे|कब)\s+(करूं|करें|लगाएं)",
                r"(कौन सा|किस)\s+(दवा|बीज|खाद)",
                r"(उपाय|समाधान|सलाह)\s+(बताएं|चाहिए)"
            ],
            "product_inquiry": [
                r"(कौन सा|किस)\s+(प्रोडक्ट|उत्पाद|बीज|दवा)",
                r"(कीमत|दाम|रेट)\s+(क्या|कितना)",
                r"(कहाँ|कैसे)\s+(मिलेगा|खरीदें)"
            ]
        }
    
    def detect_intent(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect farmer's intent from transcribed text
        
        Args:
            text: Transcribed speech text
            context: Conversation context (previous intents, crop info, etc.)
            
        Returns:
            {
                "primary_intent": str,
                "confidence": float,
                "secondary_intents": List[Tuple[str, float]],
                "entities": Dict[str, Any],
                "requires_clarification": bool
            }
        """
        text_lower = text.lower()
        
        # Score each intent
        intent_scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = self._calculate_intent_score(text_lower, keywords)
            if score > 0:
                intent_scores[intent] = score
        
        # Apply context boost
        if context:
            intent_scores = self._apply_context_boost(intent_scores, context)
        
        # Sort by score
        sorted_intents = sorted(
            intent_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        if not sorted_intents:
            return {
                "primary_intent": FarmerIntent.UNCLEAR,
                "confidence": 0.0,
                "secondary_intents": [],
                "entities": {},
                "requires_clarification": True
            }
        
        primary_intent, primary_score = sorted_intents[0]
        secondary_intents = sorted_intents[1:3] if len(sorted_intents) > 1 else []
        
        # Extract entities
        entities = self._extract_entities(text, primary_intent)
        
        # Check if clarification needed
        requires_clarification = (
            primary_score < 0.5 or
            (len(secondary_intents) > 0 and secondary_intents[0][1] > primary_score * 0.8)
        )
        
        return {
            "primary_intent": primary_intent,
            "confidence": primary_score,
            "secondary_intents": secondary_intents,
            "entities": entities,
            "requires_clarification": requires_clarification
        }
    
    def _calculate_intent_score(self, text: str, keywords: List[str]) -> float:
        """Calculate intent score based on keyword matching"""
        score = 0.0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if keyword.lower() in text:
                # Exact match
                score += 1.0
            elif any(kw in text for kw in keyword.split()):
                # Partial match
                score += 0.5
        
        # Normalize score
        return min(score / total_keywords, 1.0) if total_keywords > 0 else 0.0
    
    def _apply_context_boost(
        self,
        intent_scores: Dict[str, float],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Boost intent scores based on conversation context"""
        boosted_scores = intent_scores.copy()
        
        # If previous intent was problem-related, boost related intents
        prev_intent = context.get("previous_intent")
        if prev_intent in [
            FarmerIntent.PEST_PROBLEM,
            FarmerIntent.DISEASE_PROBLEM,
            FarmerIntent.NUTRIENT_PROBLEM
        ]:
            if FarmerIntent.CROP_ADVICE in boosted_scores:
                boosted_scores[FarmerIntent.CROP_ADVICE] *= 1.3
            if FarmerIntent.PRODUCT_INFO in boosted_scores:
                boosted_scores[FarmerIntent.PRODUCT_INFO] *= 1.2
        
        # If crop mentioned, boost crop-related intents
        if context.get("crop"):
            crop_intents = [
                FarmerIntent.CROP_ADVICE,
                FarmerIntent.PEST_PROBLEM,
                FarmerIntent.DISEASE_PROBLEM
            ]
            for intent in crop_intents:
                if intent in boosted_scores:
                    boosted_scores[intent] *= 1.2
        
        return boosted_scores
    
    def _extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """Extract entities from text based on intent"""
        entities = {}
        text_lower = text.lower()
        
        # Extract crop mentions
        crops = [
            "धान", "गेहूं", "मक्का", "बाजरा", "ज्वार",
            "चना", "मटर", "सरसों", "सोयाबीन",
            "टमाटर", "बैंगन", "मिर्च", "प्याज", "आलू",
            "rice", "wheat", "maize", "corn", "tomato", "chilli"
        ]
        for crop in crops:
            if crop in text_lower:
                entities["crop"] = crop
                break
        
        # Extract pest/disease names
        if intent in [FarmerIntent.PEST_PROBLEM, FarmerIntent.DISEASE_PROBLEM]:
            pests = ["माहू", "सुंडी", "इल्ली", "टिड्डी", "thrip", "aphid", "borer"]
            for pest in pests:
                if pest in text_lower:
                    entities["pest_name"] = pest
                    break
        
        # Extract numbers (areas, quantities)
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers:
            entities["numbers"] = numbers
        
        # Extract product names
        products = ["यूरिया", "डीएपी", "एनपीके", "urea", "dap", "npk"]
        for product in products:
            if product in text_lower:
                entities["product"] = product
                break
        
        return entities


# Global instance
intent_service = IntentDetectionService()
