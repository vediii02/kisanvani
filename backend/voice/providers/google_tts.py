"""
Google Cloud Text-to-Speech Provider for Kisan Vani AI
Uses Google Cloud TTS REST API with API key
"""

import os
import io
import logging
import aiohttp
import base64
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# Define BaseTTSProvider here to avoid circular import
class BaseTTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, language: str = 'hi') -> bytes:
        pass


class GoogleTTSProvider(BaseTTSProvider):
    """Google Cloud Text-to-Speech provider using REST API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_name: str = "hi-IN-Wavenet-A",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        audio_encoding: str = "LINEAR16"
    ):
        self.api_key = api_key or os.getenv('GOOGLE_TTS_API_KEY')
        self.voice_name = voice_name
        self.speaking_rate = speaking_rate
        self.pitch = pitch
        self.audio_encoding = audio_encoding
        self.api_url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"
        
        if not self.api_key:
            logger.warning("⚠️ No Google TTS API key provided - TTS will fail")
        else:
            logger.info(f"✅ Google Cloud TTS initialized with API key (voice: {voice_name})")
    
    async def synthesize(self, text: str, language: str = 'hi') -> bytes:
        """Convert text to speech using Google Cloud TTS REST API"""
        
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return b""
        
        if not self.api_key:
            logger.error("❌ No API key - cannot synthesize")
            return b""
        
        # Truncate if too long
        MAX_LENGTH = 5000
        if len(text) > MAX_LENGTH:
            logger.warning(f"Text too long ({len(text)} chars), truncating")
            text = text[:MAX_LENGTH]
        
        try:
            # Language mapping for Google Cloud TTS
            language_map = {
                'hi': 'hi-IN',
                'hi-IN': 'hi-IN',
                'en': 'en-IN',
                'en-IN': 'en-IN',
                'en-US': 'en-US'
            }
            lang_code = language_map.get(language, 'hi-IN')
            
            # Build request payload
            payload = {
                "input": {"text": text},
                "voice": {
                    "languageCode": lang_code,
                    "name": self.voice_name
                },
                "audioConfig": {
                    "audioEncoding": self.audio_encoding,
                    "speakingRate": self.speaking_rate,
                    "pitch": self.pitch
                }
            }
            
            logger.info(f"🎤 Synthesizing with Google Cloud TTS: '{text[:50]}...' | Voice: {self.voice_name}")
            
            # Make async request
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Google TTS API error ({response.status}): {error_text}")
                        return b""
                    
                    result = await response.json()
                    audio_content = base64.b64decode(result['audioContent'])
                    
                    logger.info(f"✅ Synthesized {len(audio_content):,} bytes with Google Cloud TTS")
                    return audio_content
            
        except Exception as e:
            logger.error(f"❌ Google Cloud TTS synthesis failed: {e}")
            return b""
    
    def get_available_voices(self, language_code: str = 'hi-IN') -> list:
        """Get list of available voices from Google Cloud TTS"""
        # Common Hindi voices
        if language_code.startswith('hi'):
            return [
                'hi-IN-Wavenet-A', 'hi-IN-Wavenet-B', 'hi-IN-Wavenet-C', 'hi-IN-Wavenet-D',
                'hi-IN-Standard-A', 'hi-IN-Standard-B', 'hi-IN-Standard-C', 'hi-IN-Standard-D'
            ]
        # Common English (India) voices
        elif language_code.startswith('en'):
            return [
                'en-IN-Wavenet-A', 'en-IN-Wavenet-B', 'en-IN-Wavenet-C', 'en-IN-Wavenet-D',
                'en-IN-Standard-A', 'en-IN-Standard-B', 'en-IN-Standard-C', 'en-IN-Standard-D'
            ]
        return ['hi-IN-Wavenet-A']
