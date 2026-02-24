"""
Text-to-Speech Service Wrapper
Wraps Google TTS provider with gTTS fallback
"""

import logging
from typing import Dict, Optional
from voice.providers.google_tts import GoogleTTSProvider
from gtts import gTTS
import io
import os

logger = logging.getLogger(__name__)


class TTSService:
    """Unified TTS service wrapper with fallback"""
    
    def __init__(self):
        """Initialize TTS with Google TTS provider and gTTS fallback"""
        try:
            self.provider = GoogleTTSProvider()
            logger.info("TTS Service initialized with Google Cloud TTS")
        except Exception as e:
            logger.warning(f"Google TTS initialization failed, will use gTTS fallback: {e}")
            self.provider = None
    
    async def _synthesize_with_gtts(self, text: str, language: str) -> bytes:
        """Fallback TTS using gTTS (no API key needed)"""
        try:
            logger.info("Using gTTS fallback for synthesis")
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to BytesIO
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            
            return audio_fp.read()
        except Exception as e:
            logger.error(f"gTTS synthesis failed: {e}")
            return b""
    
    async def synthesize_speech(
        self,
        text: str,
        language: str = "hi",
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            language: Language code (hi, en)
            session_id: Session ID for file naming
            
        Returns:
            {
                "success": bool,
                "audio_url": str,
                "audio_bytes": bytes (optional),
                "error": str (if failed)
            }
        """
        try:
            audio_bytes = None
            
            # Try Google Cloud TTS first
            if self.provider:
                try:
                    audio_bytes = await self.provider.synthesize(
                        text=text,
                        language=language
                    )
                    if audio_bytes:
                        logger.info("✅ Synthesized with Google Cloud TTS")
                except Exception as e:
                    logger.warning(f"Google Cloud TTS failed, trying gTTS fallback: {e}")
            
            # Fallback to gTTS if Google TTS failed or not available
            if not audio_bytes:
                audio_bytes = await self._synthesize_with_gtts(text, language)
                if audio_bytes:
                    logger.info("✅ Synthesized with gTTS fallback")
            
            if not audio_bytes:
                return {
                    "success": False,
                    "audio_url": "",
                    "error": "Failed to generate audio with both providers"
                }
            
            # Save audio file
            audio_filename = f"response_{session_id or 'temp'}.mp3"
            audio_dir = "static/audio"
            os.makedirs(audio_dir, exist_ok=True)
            
            audio_path = os.path.join(audio_dir, audio_filename)
            
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
            
            # Generate full URL (for Exotel integration)
            base_url = os.getenv("BASE_URL", "https://kisan.rechargestudio.com")
            audio_url = f"{base_url}/static/audio/{audio_filename}"
            
            return {
                "success": True,
                "audio_url": audio_url,
                "audio_bytes": audio_bytes
            }
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return {
                "success": False,
                "audio_url": "",
                "error": str(e)
            }
