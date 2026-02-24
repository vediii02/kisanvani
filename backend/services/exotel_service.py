"""
Exotel Integration Service
Handles real phone calls via Exotel API
"""

import os
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class ExotelService:
    """Exotel API integration for phone calls"""
    
    def __init__(self):
        self.api_key = os.getenv("EXOTEL_API_KEY", "")
        self.api_token = os.getenv("EXOTEL_API_TOKEN", "")
        self.sid = os.getenv("EXOTEL_SID", "")
        self.base_url = f"https://api.exotel.com/v1/Accounts/{self.sid}"
        self.callback_url = os.getenv("EXOTEL_CALLBACK_URL", "")
        self.use_mock = os.getenv("USE_MOCK_EXOTEL", "true").lower() == "true"
        
    async def make_call(
        self,
        from_number: str,
        to_number: str,
        call_type: str = "trans",
        custom_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate outbound call via Exotel
        
        Args:
            from_number: Exotel virtual number
            to_number: Farmer's phone number
            call_type: "trans" (transactional) or "promo" (promotional)
            custom_field: Custom data to pass (e.g., call_session_id)
            
        Returns:
            {
                "success": bool,
                "call_sid": str,
                "status": str,
                "error": Optional[str]
            }
        """
        if self.use_mock:
            return await self._mock_make_call(from_number, to_number)
        
        try:
            url = f"{self.base_url}/Calls/connect.json"
            
            data = {
                "From": from_number,
                "To": to_number,
                "CallerId": from_number,
                "CallType": call_type,
                "Url": f"{self.callback_url}/api/exotel/voice",  # Voice webhook
                "StatusCallback": f"{self.callback_url}/api/exotel/status",  # Status webhook
            }
            
            if custom_field:
                data["CustomField"] = custom_field
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    auth=(self.api_key, self.api_token),
                    data=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    call_data = result.get("Call", {})
                    
                    return {
                        "success": True,
                        "call_sid": call_data.get("Sid"),
                        "status": call_data.get("Status"),
                        "error": None
                    }
                else:
                    logger.error(f"Exotel API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "call_sid": None,
                        "status": "failed",
                        "error": f"API error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Exotel make_call failed: {e}", exc_info=True)
            return {
                "success": False,
                "call_sid": None,
                "status": "failed",
                "error": str(e)
            }
    
    async def handle_incoming_call(self, call_data: Dict[str, Any]) -> str:
        """
        Handle incoming call webhook from Exotel
        Returns NCCO (Call Flow XML)
        
        Args:
            call_data: Webhook data from Exotel
            
        Returns:
            XML response for call flow
        """
        call_sid = call_data.get("CallSid")
        from_number = call_data.get("From")
        to_number = call_data.get("To")
        
        logger.info(f"Incoming call: {call_sid} from {from_number} to {to_number}")
        
        # Generate initial response XML
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="hi-IN">
        नमस्ते! मैं किसान AI हूं, आपकी खेती सहायक।
        कृपया अपनी समस्या बताएं।
    </Say>

    <Record
        action="https://conjugative-tandra-amitotically.ngrok-free.dev/webhooks/exotel/gather"
        method="POST"
        maxLength="60"
        finishOnKey="#"
        playBeep="true"
    />
</Response>"""
        
        return xml
    
    async def handle_gather(self, gather_data: Dict[str, Any]) -> str:
        """
        Handle user input (speech or DTMF)
        
        Args:
            gather_data: Gathered input from Exotel
            
        Returns:
            XML response with next action
        """
        recording_url = gather_data.get("RecordingUrl")
        digits = gather_data.get("Digits")
        
        if recording_url:
            # Process speech recording
            logger.info(f"Processing speech: {recording_url}")
            # TODO: Download and transcribe recording
            
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="hi-IN">
        आपकी समस्या मिल गई। हम जल्द ही मदद करेंगे।
    </Say>
    <Hangup/>
</Response>"""
        
        return xml
    
    async def handle_status_callback(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle call status updates from Exotel
        
        Args:
            status_data: Status webhook data
            
        Returns:
            Processed status information
        """
        call_sid = status_data.get("CallSid")
        call_status = status_data.get("Status")
        duration = status_data.get("Duration", 0)
        
        logger.info(f"Call {call_sid} status: {call_status}, duration: {duration}s")
        
        return {
            "call_sid": call_sid,
            "status": call_status,
            "duration": int(duration),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def play_audio(self, audio_url: str) -> str:
        """
        Generate XML to play audio file
        
        Args:
            audio_url: URL of audio file to play
            
        Returns:
            XML with Play directive
        """
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
</Response>"""
        
        return xml
    
    async def record_audio(
        self,
        max_length: int = 60,
        finish_on_key: str = "#",
        callback_url: Optional[str] = None
    ) -> str:
        """
        Generate XML to record audio
        
        Args:
            max_length: Maximum recording length in seconds
            finish_on_key: Key to finish recording
            callback_url: URL to send recording to
            
        Returns:
            XML with Record directive
        """
        callback = callback_url or f"{self.callback_url}/api/exotel/recording"
        
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Record maxLength="{max_length}" 
            finishOnKey="{finish_on_key}"
            action="{callback}"
            method="POST">
    </Record>
</Response>"""
        
        return xml
    
    def verify_webhook(self, signature: str, url: str, params: Dict[str, Any]) -> bool:
        """
        Verify Exotel webhook signature
        
        Args:
            signature: X-Exotel-Signature header
            url: Full webhook URL
            params: Request parameters
            
        Returns:
            True if signature is valid
        """
        if self.use_mock:
            return True
        
        try:
            # Sort parameters
            sorted_params = sorted(params.items())
            
            # Create string to sign
            data = url + "".join([f"{k}{v}" for k, v in sorted_params])
            
            # Calculate HMAC
            expected_signature = hmac.new(
                self.api_token.encode(),
                data.encode(),
                hashlib.sha1
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Webhook verification failed: {e}")
            return False
    
    async def _mock_make_call(self, from_number: str, to_number: str) -> Dict[str, Any]:
        """Mock call for testing"""
        import uuid
        
        return {
            "success": True,
            "call_sid": f"MOCK_{uuid.uuid4().hex[:16]}",
            "status": "in-progress",
            "error": None
        }
    
    async def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        """
        Get call details from Exotel
        
        Args:
            call_sid: Call SID
            
        Returns:
            Call details
        """
        if self.use_mock:
            return {
                "success": True,
                "call_sid": call_sid,
                "status": "completed",
                "duration": 120,
                "recording_url": None
            }
        
        try:
            url = f"{self.base_url}/Calls/{call_sid}.json"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    auth=(self.api_key, self.api_token),
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    call_data = result.get("Call", {})
                    
                    return {
                        "success": True,
                        "call_sid": call_data.get("Sid"),
                        "status": call_data.get("Status"),
                        "duration": call_data.get("Duration"),
                        "recording_url": call_data.get("RecordingUrl")
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Get call details failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
exotel_service = ExotelService()
