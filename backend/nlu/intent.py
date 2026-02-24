import re
from typing import Dict, List

INTENT_PATTERNS = {
    'crop_disease': [
        r'(बीमारी|रोग)',
        r'(पीला|पत्ते)',
        r'disease',
    ],
    'pest_control': [
        r'(कीट|पतंग)',
        r'pest',
        r'insect',
    ],
    'fertilizer': [
        r'(खाद|उर्वरक)',
        r'fertilizer',
    ],
    'irrigation': [
        r'(पानी|सिंचाई)',
        r'water',
        r'irrigation',
    ],
    'general_query': [
        r'.*'
    ]
}

def detect_intent(text: str) -> str:
    text_lower = text.lower()
    
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return intent
    
    return 'general_query'