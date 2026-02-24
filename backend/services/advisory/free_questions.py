import requests
from typing import Optional, Dict, Any

class AdvisoryAPIError(Exception):
    pass

class AdvisoryService:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def get_advisory(self, crop: str, problem: str, language: str = "hi", location: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "crop": crop,
            "problem": problem,
            "language": language
        }
        if location:
            payload["location"] = location
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data:
                raise AdvisoryAPIError("Empty response from advisory API")
            return data
        except Exception as e:
            raise AdvisoryAPIError(f"Failed to fetch advisory: {e}")
