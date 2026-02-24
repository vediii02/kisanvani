import re

def normalize_hindi_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def detect_language(text: str) -> str:
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    if hindi_chars > english_chars:
        return 'hi'
    else:
        return 'en'