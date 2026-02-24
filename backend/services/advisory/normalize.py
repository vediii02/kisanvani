from typing import Any, Dict, Optional

def normalize_advisory_response(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalize the advisory API response to a structured object.
    Returns None if the response is empty or invalid.
    """
    if not raw or not isinstance(raw, dict):
        return None
    # Example normalization logic (adjust keys as per actual API response)
    return {
        "issue": raw.get("issue") or raw.get("disease"),
        "treatment": raw.get("treatment_steps") or raw.get("treatment"),
        "recommendations": raw.get("recommendations"),
        "fertilizer": raw.get("fertilizer"),
        "spray": raw.get("spray"),
        "dosage": raw.get("dosage"),
        "timing": raw.get("timing"),
        "prevention": raw.get("prevention"),
        "raw": raw
    }
