import re
from typing import Dict, Optional

CROP_KEYWORDS = {
    'wheat': ['गेहूं', 'wheat'],
    'rice': ['धान', 'rice'],
    'soybean': ['सोयाबीन', 'soybean'],
    'cotton': ['कपास', 'cotton'],
    'maize': ['मक्का', 'maize', 'corn'],
}

def extract_crop(text: str) -> Optional[str]:
    text_lower = text.lower()
    
    for crop, keywords in CROP_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return crop
    
    return None


def extract_farmer_name(text: str) -> Optional[str]:
    """
    Extract farmer's name from text.
    Handles patterns like:
    - "mera naam X hai"
    - "main X hoon"
    - Direct name
    """
    text = text.strip()
    
    # Patterns to detect name (more specific patterns first)
    patterns = [
        r'(?:मेरा नाम|नाम)\s+([^\s,]+(?:\s+[^\s,]+)?)\s+(?:है|hai)',
        r'(?:मैं|main|mai)\s+([^\s,]+(?:\s+[^\s,]+)?)\s+(?:हूं|हूँ|hoon|hun)(?!.*(?:बोल|bol))',
        r'([^\s,]+(?:\s+[^\s,]+)?)\s+(?:बोल रहा|बोल रही|bol raha|bol rahi)',
        r'(?:नाम|naam|name)\s+([^\s,]+(?:\s+[^\s,]+)?)\s+(?:है|hai)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up common words at the end
            name = re.sub(r'\s+(है|हैं|से|में|गांव|गाँव|जिला|hai|hain|se|mein|gaon|jila).*$', '', name, flags=re.IGNORECASE)
            # Check if valid name (2-50 chars, no numbers, 1-3 words)
            if len(name) >= 2 and len(name) <= 50 and not re.search(r'\d', name):
                words = name.split()
                if len(words) <= 3:
                    return name
    
    return None


def extract_village_name(text: str) -> Optional[str]:
    """
    Extract village name from text.
    Handles patterns like:
    - "gaon X hai"
    - "X gaon se"
    """
    text = text.strip()
    
    patterns = [
        r'(?:गांव|गाँव|village|gaon|gaav)\s+([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+)?)\s+(?:है|hai)',
        r'(?:गांव|गाँव|village|gaon|gaav)\s+([A-Za-z\u0900-\u097F]+)(?![A-Za-z\u0900-\u097F])',
        r'([A-Za-z\u0900-\u097F]+)\s+(?:गांव|गाँव|village|gaon|gaav)',
        r'([A-Za-z\u0900-\u097F]+)\s+(?:गांव|गाँव)\s+(?:से|se)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            village = match.group(1).strip()
            # Remove common trailing words
            village = re.sub(r'\s+(से|se)$', '', village, flags=re.IGNORECASE)
            # Check if valid village name (2-50 chars, only letters, 1-2 words)
            if len(village) >= 2 and len(village) <= 50:
                words = village.split()
                if len(words) <= 2 and village not in ['से', 'se', 'में', 'mein']:
                    return village
    
    return None


def extract_district_name(text: str) -> Optional[str]:
    """
    Extract district name from text.
    """
    text = text.strip()
    
    patterns = [
        r'(?:जिला|district|jila)\s+([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+)?)',
        r'([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+)?)\s+(?:जिला|district|jila)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            district = match.group(1).strip()
            # Remove trailing common words
            district = re.sub(r'\s+(है|से|में|हूं|hai|se|mein|hoon)$', '', district, flags=re.IGNORECASE)
            # Check if valid district name (2-50 chars, only letters, 1-3 words)
            if len(district) >= 2 and len(district) <= 50:
                words = district.split()
                if len(words) <= 3:
                    return district
    
    return None


def extract_state_name(text: str) -> Optional[str]:
    """
    Extract state name from text.
    """
    text = text.strip()
    
    # Common state names and patterns
    patterns = [
        r'(?:राज्य|state)\s+([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+){0,2})',
        r'([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+){0,2})\s+(?:राज्य|pradesh)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            state = match.group(1).strip()
            # Remove trailing words
            state = re.sub(r'\s+(है|से|में|hai|se|mein)$', '', state, flags=re.IGNORECASE)
            # Check if valid state name (2-50 chars, 1-3 words)
            if len(state) >= 2 and len(state) <= 50:
                words = state.split()
                if len(words) <= 3:
                    return state
    
    # Check for common state names without keywords
    common_states = ['उत्तर प्रदेश', 'uttar pradesh', 'मध्य प्रदेश', 'madhya pradesh', 
                     'महाराष्ट्र', 'maharashtra', 'पंजाब', 'punjab', 'हरियाणा', 'haryana',
                     'राजस्थान', 'rajasthan', 'बिहार', 'bihar', 'गुजरात', 'gujarat']
    
    text_lower = text.lower()
    for state in common_states:
        if state in text_lower:
            # Extract the matching portion
            idx = text_lower.find(state)
            extracted = text[idx:idx+len(state)]
            return extracted
    
    return None


def extract_crop_type(text: str) -> Optional[str]:
    """
    Extract crop type being grown by farmer.
    """
    return extract_crop(text)  # Reuse existing crop extraction


def extract_land_size(text: str) -> Optional[str]:
    """
    Extract land size from text.
    Handles patterns like:
    - "5 acre"
    - "2 bigha"
    - "10 hectare"
    """
    text = text.strip()
    
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:acre|एकड़|bigha|बीघा|hectare|हेक्टेयर)',
        r'(?:acre|एकड़|bigha|बीघा|hectare|हेक्टेयर)\s*(\d+(?:\.\d+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    # Just numbers with units
    match = re.search(r'\d+(?:\.\d+)?\s*(?:acre|एकड़|bigha|बीघा|hectare|हेक्टेयर|एकर)', text, re.IGNORECASE)
    if match:
        return match.group(0)
    
    return None


def extract_all_farmer_entities(text: str) -> Dict[str, Optional[str]]:
    """
    Extract all possible farmer-related entities from text.
    Returns a dictionary with all extracted information.
    """
    # Extract crop_age_days (e.g. "फसल की उम्र 45 दिन है", "crop age is 30 days", "45 din")
    import re
    crop_age_days = None
    patterns = [
        r'(?:फसल की उम्र|crop age|उम्र|age)\s*:?\s*(\d{1,3})\s*(?:दिन|days|din)?',
        r'(\d{1,3})\s*(?:दिन|days|din)\s*(?:की उम्र|old|age)?'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            crop_age_days = match.group(1)
            break

    return {
        'name': extract_farmer_name(text),
        'village': extract_village_name(text),
        'district': extract_district_name(text),
        'state': extract_state_name(text),
        'crop_type': extract_crop_type(text),
        'land_size': extract_land_size(text),
        'crop': extract_crop(text),
        'crop_age_days': crop_age_days
    }