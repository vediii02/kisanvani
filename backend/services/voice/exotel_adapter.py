import base64
import json
import audioop
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class ExotelAdapter:
    """
    Adapter to bridge Exotel's WebSocket protocol with the AI Voice Pipeline.
    Auto-detects audio encoding from the start event's media_format.
    """
    
    def __init__(self):
        self.stream_sid: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.from_number: Optional[str] = None
        self.to_number: Optional[str] = None
        self.custom_parameters: dict = {}
        self.is_mulaw: bool = False  # Default: PCM16 (128kbps at 8kHz)

    def parse_message(self, message_text: str) -> Tuple[Optional[str], Optional[bytes]]:
        """
        Parses incoming Exotel WebSocket text messages.
        
        Returns:
            (event_type, audio_pcm_bytes)
        """
        try:
            data = json.loads(message_text)
            event = data.get("event")
            
            if event == "connected":
                logger.info("Exotel connection acknowledged")
                return "connected", None

            if event == "start":
                start_data = data.get("start", {})
                self.stream_sid = data.get("stream_sid") or data.get("streamSid") or start_data.get("stream_sid")
                self.call_sid = start_data.get("call_sid") or start_data.get("callSid")
                self.from_number = start_data.get("from")
                self.to_number = start_data.get("to")
                self.custom_parameters = start_data.get("custom_parameters", {})
                
                # Auto-detect audio codec from media_format
                media_format = start_data.get("media_format", {})
                bit_rate = media_format.get("bit_rate", "128kbps")
                # 64kbps at 8kHz = 8-bit µ-law; 128kbps at 8kHz = 16-bit PCM
                self.is_mulaw = "64" in str(bit_rate)
                
                codec = "µ-law (G.711)" if self.is_mulaw else "PCM16"
                logger.info(f"Exotel Stream Started: StreamSid={self.stream_sid}, CallSid={self.call_sid}")
                logger.info(f"Exotel from={self.from_number}, to={self.to_number}, codec={codec}, params={self.custom_parameters}")
                return "start", None
                
            elif event == "media":
                media = data.get("media", {})
                payload = media.get("payload")
                if payload:
                    raw_bytes = base64.b64decode(payload)
                    if self.is_mulaw:
                        # Convert µ-law to 16-bit PCM
                        pcm_bytes = audioop.ulaw2lin(raw_bytes, 2)
                    else:
                        # Already PCM16, pass through
                        pcm_bytes = raw_bytes
                    return "media", pcm_bytes
            
            elif event == "stop":
                logger.info(f"Exotel Stream Stopped: {self.stream_sid}")
                return "stop", None
            
            else:
                logger.info(f"Exotel event '{event}': {json.dumps(data, default=str)[:200]}")
                
            return event, None
            
        except Exception as e:
            logger.error(f"Error parsing Exotel message: {e}, raw: {message_text[:200]}")
            return None, None

    def format_audio_message(self, pcm_bytes: bytes) -> str:
        """
        Converts PCM bytes from the pipeline to an Exotel-compatible JSON media message.
        """
        if not self.stream_sid:
            logger.warning("Attempted to format audio message without a valid StreamSid")
            return ""
            
        try:
            if self.is_mulaw:
                # Convert PCM (16-bit) to µ-law (8-bit)
                out_bytes = audioop.lin2ulaw(pcm_bytes, 2)
            else:
                # Already PCM16, pass through
                out_bytes = pcm_bytes
            
            payload = base64.b64encode(out_bytes).decode("utf-8")
            message = {
                "event": "media",
                "streamSid": self.stream_sid,
                "stream_sid": self.stream_sid,
                "media": {
                    "payload": payload
                }
            }
            return json.dumps(message)
        except Exception as e:
            logger.error(f"Error formatting Exotel audio message: {e}")
            return ""

    def format_barge_in_message(self) -> str:
        """
        Formats a 'clear' message to signal Exotel to stop playing current audio.
        """
        if not self.stream_sid:
            return ""
        
        return json.dumps({
            "event": "clear",
            "streamSid": self.stream_sid,
            "stream_sid": self.stream_sid
        })
