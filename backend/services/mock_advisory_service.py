"""
Mock Advisory Service - Works without OpenAI API
Provides wheat-related answers without requiring API quota
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MockAdvisoryService:
    """
    Provides mock advisory responses for common wheat problems
    Used when OpenAI API is not available or quota exceeded
    """
    
    def __init__(self):
        # Multiple keywords can map to same answer
        self.wheat_kb = {
            # Yellow leaf problems
            "पीले पत्ते|पीली पत्तियां|yellow leaves": {
                "advisory": "गेहूं में पीले पत्ते नाइट्रोजन की कमी के लक्षण हैं। यूरिया खाद 100 किलो प्रति एकड़ डालें। पहली सिंचाई के समय 50% और दूसरी सिंचाई के समय 50% यूरिया डालें। साथ ही मिट्टी की जांच कराएं।",
                "keywords": ["पीले पत्ते", "पीली पत्तियां", "पत्ते पीले"],
                "confidence": 0.85
            },
            # Rust diseases
            "रतुआ|रतुआ रोग|rust|पीला रतुआ|भूरा रतुआ|काला रतुआ": {
                "advisory": "गेहूं में रतुआ रोग तीन प्रकार का होता है: पीला रतुआ (पत्तियों पर पीले धब्बे), भूरा रतुआ (भूरे-नारंगी धब्बे), काला रतुआ (काले धब्बे)। उपचार: प्रोपिकोनाजोल 25% EC @ 1 मिली/लीटर या टेबुकोनाजोल 25% EC @ 1 मिली/लीटर पानी में मिलाकर छिड़काव करें। 15 दिन बाद दोबारा स्प्रे करें। रोग प्रतिरोधी किस्में जैसे HD-2967, WH-1105 लगाएं।",
                "keywords": ["रतुआ", "रतुआ रोग", "पीला रतुआ", "भूरा रतुआ", "काला रतुआ", "rust"],
                "confidence": 0.90
            },
            # Brown spots
            "भूरे धब्बे|भूरे पत्ते|leaf blight": {
                "advisory": "गेहूं में भूरे धब्बे पत्ती झुलसा रोग (Leaf Blight) के लक्षण हैं। मैंकोजेब 75% WP @ 2 ग्राम/लीटर पानी में मिलाकर छिड़काव करें। 10-12 दिन बाद दोबारा छिड़काव करें। खेत में जल निकासी की व्यवस्था करें।",
                "keywords": ["भूरे धब्बे", "भूरे पत्ते", "पत्ती झुलसा"],
                "confidence": 0.88
            },
            # Black spots
            "काले धब्बे|करनाल बंट|karnal bunt": {
                "advisory": "गेहूं में काले धब्बे करनाल बंट या काला रतुआ रोग के लक्षण हो सकते हैं। प्रोपिकोनाजोल 1 मिली/लीटर पानी में मिलाकर छिड़काव करें। बीज उपचार विटावैक्स पावर @ 2.5 ग्राम/किलो बीज से करें। रोग प्रतिरोधी किस्में लगाएं।",
                "keywords": ["काले धब्बे", "करनाल बंट", "black spot"],
                "confidence": 0.82
            },
            # Late sowing
            "देरी से बुवाई|देरी से बोना|late sowing|देर से": {
                "advisory": "देरी से बोए गए गेहूं के लिए शीघ्र पकने वाली किस्में चुनें: DBW-187 (110 दिन), HD-3086 (115 दिन), PBW-725 (120 दिन)। देखभाल: बीज दर 25% बढ़ाएं (125-130 किलो/हेक्टेयर), पहली सिंचाई 15-20 दिन में दें, यूरिया की पूरी मात्रा 2 बार में (20 दिन और 40 दिन पर) दें। गर्मी से बचाव के लिए आखिरी सिंचाई दाना भरते समय जरूर दें।",
                "keywords": ["देरी से बुवाई", "देर से बोना", "लेट सोइंग", "देरी"],
                "confidence": 0.92
            },
            # Insect pests
            "कीड़े|कीट|insects|pest": {
                "advisory": "गेहूं में मुख्य कीट: माहू (Aphid) - इमिडाक्लोप्रिड 0.5 मिली/लीटर, दीमक - क्लोरपायरीफॉस 2.5 मिली/लीटर मिट्टी उपचार, आर्मीवर्म - क्लोरपायरीफॉस 2 मिली/लीटर शाम को छिड़काव। जैविक उपाय: नीम तेल 5 मिली/लीटर का छिड़काव। कीट प्रकाश जाल (Light Trap) लगाएं।",
                "keywords": ["कीड़े", "कीट", "माहू", "दीमक", "इल्ली"],
                "confidence": 0.86
            },
            # Root rot
            "जड़ सड़न|जड़ गलन|root rot": {
                "advisory": "गेहूं में जड़ सड़न अधिक पानी या फफूंद रोग के कारण होती है। उपचार: ट्राइकोडर्मा विरडी 5 ग्राम/किलो बीज की दर से बीज उपचार करें। खेत में जल निकासी की व्यवस्था करें। अधिक सिंचाई से बचें। कार्बेंडाजिम 1 ग्राम/लीटर का मिट्टी उपचार करें।",
                "keywords": ["जड़ सड़न", "जड़ गलन", "root rot"],
                "confidence": 0.84
            },
            # Irrigation
            "सिंचाई|पानी|irrigation|कितना पानी": {
                "advisory": "गेहूं में 4-6 सिंचाई की आवश्यकता होती है। समय: पहली सिंचाई बुवाई के 20-25 दिन बाद (CRI stage - ताज जड़ बनने पर), दूसरी 40-45 दिन बाद (कल्ले फूटने पर), तीसरी 60-65 दिन बाद (गांठें बनने पर), चौथी 80-85 दिन बाद (फूल आने पर), पांचवी 100-105 दिन बाद (दाना भरने पर)। हर सिंचाई में 5-7 सेमी पानी दें।",
                "keywords": ["सिंचाई", "पानी", "irrigation", "सींचना"],
                "confidence": 0.90
            },
            # Fertilizer
            "खाद|उर्वरक|fertilizer|यूरिया|dap": {
                "advisory": "गेहूं के लिए खाद की मात्रा (प्रति हेक्टेयर): नाइट्रोजन 120 किलो, फॉस्फोरस 60 किलो, पोटाश 40 किलो। प्रयोग: DAP 130 किलो + MOP 65 किलो बुवाई के समय, यूरिया 3 बार में - पहली बार 65 किलो (20-25 दिन), दूसरी बार 65 किलो (40-45 दिन), तीसरी बार 65 किलो (60-65 दिन)। जिंक सल्फेट 25 किलो बुवाई से पहले मिट्टी में मिलाएं।",
                "keywords": ["खाद", "उर्वरक", "यूरिया", "dap", "fertilizer"],
                "confidence": 0.92
            },
            # Sowing/Planting
            "बुवाई|बोना|sowing|variety|किस्म": {
                "advisory": "गेहूं की बुवाई का सही समय: अक्टूबर के अंत से नवंबर के मध्य तक (समय पर), दिसंबर प्रथम सप्ताह तक (देरी से)। उन्नत किस्में: समय पर बुवाई - HD-2967, PBW-725, DBW-303 | देरी से बुवाई - HD-3086, DBW-187, PBW-590। बीज दर 100-125 किलो/हेक्टेयर। कतारों के बीच 20-22 सेमी दूरी। बीज 5-6 सेमी गहराई पर बोएं। बीज उपचार विटावैक्स @ 2.5 ग्राम/किलो जरूर करें।",
                "keywords": ["बुवाई", "बोना", "किस्म", "variety", "sowing"],
                "confidence": 0.91
            },
            # Weed control
            "खरपतवार|weed|घास": {
                "advisory": "गेहूं में खरपतवार नियंत्रण: चौड़ी पत्ती वाले खरपतवार - 2,4-D सोडियम साल्ट @ 500 ग्राम/एकड़ बुवाई के 30-35 दिन बाद। संकरी पत्ती वाले - Clodinafop 60 ग्राम/एकड़ बुवाई के 25-30 दिन बाद। मिश्रित खरपतवार - Sulfosulfuron 25 ग्राम/एकड़। निराई-गुड़ाई: पहली बुवाई के 20-25 दिन बाद, दूसरी 40-45 दिन बाद।",
                "keywords": ["खरपतवार", "weed", "घास", "निराई"],
                "confidence": 0.87
            },
            # Disease general
            "रोग|disease|बीमारी": {
                "advisory": "गेहूं के मुख्य रोग: 1) रतुआ (पीला/भूरा/काला) - प्रोपिकोनाजोल छिड़काव, 2) करनाल बंट - बीज उपचार, 3) पत्ती झुलसा - मैंकोजेब छिड़काव, 4) जड़ सड़न - जल निकासी और ट्राइकोडर्मा। रोकथाम: प्रमाणित बीज, बीज उपचार, उचित फसल चक्र, संतुलित खाद, समय पर बुवाई।",
                "keywords": ["रोग", "disease", "बीमारी"],
                "confidence": 0.85
            }
        }
    
    async def generate_advisory(self, farmer_query: str, session_id: str = None) -> Dict[str, Any]:
        """
        Generate advisory response for wheat queries with flexible keyword matching
        """
        query_lower = farmer_query.lower()
        
        # Search for matching keywords in query - check all keywords for each entry
        best_match = None
        best_confidence = 0.0
        matched_keyword = ""
        
        for entry_key, data in self.wheat_kb.items():
            # Check if any keyword from this entry matches the query
            for keyword in data["keywords"]:
                if keyword.lower() in query_lower:
                    if data["confidence"] > best_confidence:
                        best_match = data
                        best_confidence = data["confidence"]
                        matched_keyword = keyword
                        logger.info(f"Matched keyword '{keyword}' in query: {farmer_query}")
                        break
        
        # If specific match found, return it
        if best_match:
            return {
                'advisory_text': best_match["advisory"],
                'confidence': best_match["confidence"],
                'escalated': False,
                'kb_entries': [],
                'reason': f'Matched keyword: {matched_keyword}'
            }
        
        # If no specific match found, check if it's a wheat query
        wheat_keywords = ["गेहूं", "gehu", "gehun", "wheat"]
        is_wheat_query = any(kw in query_lower for kw in wheat_keywords)
        
        if is_wheat_query:
            logger.warning(f"Wheat query but no specific match: {farmer_query}")
            return {
                'advisory_text': "गेहूं की फसल के लिए सामान्य सुझाव: समय पर बुवाई करें, प्रमाणित बीज उपयोग करें, संतुलित खाद दें, 4-6 सिंचाई करें, रोग और कीटों की निगरानी रखें। कृपया अपनी समस्या के बारे में विस्तार से बताएं - जैसे रोग का नाम, लक्षण, पत्तियों का रंग आदि।",
                'confidence': 0.65,
                'escalated': False,
                'kb_entries': [],
                'reason': 'General wheat query - no specific problem mentioned'
            }
        else:
            # Not a wheat query or unclear
            logger.warning(f"Non-wheat or unclear query: {farmer_query}")
            return {
                'advisory_text': 'कृपया अपनी समस्या के बारे में और विस्तार से बताएं। किस फसल में क्या समस्या है? लक्षण क्या हैं?',
                'confidence': 0.50,
                'escalated': True,
                'kb_entries': [],
                'reason': 'Unclear query - no wheat keywords found'
            }
