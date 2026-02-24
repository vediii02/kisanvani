"""
Speech-to-Text Service
Supports multiple STT providers: Google Cloud Speech, Bhashini, Whisper
"""

import os
import io
import logging
from typing import Optional, Dict, Any, Tuple
from enum import Enum
import httpx
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class STTProvider(str, Enum):
    GOOGLE = "google"
    BHASHINI = "bhashini"
    WHISPER = "whisper"
    MOCK = "mock"  # For testing


class STTService:
    """Unified Speech-to-Text service supporting multiple providers"""
    
    def __init__(self):
        self.provider = os.getenv("STT_PROVIDER", "google")
        self.google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "google-creds.json")
        self.bhashini_api_key = os.getenv("BHASHINI_API_KEY", "")
        self.bhashini_user_id = os.getenv("BHASHINI_USER_ID", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: str = "hi-IN",
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Audio file bytes
            audio_format: Audio format (wav, mp3, webm, etc.)
            language: Language code (hi-IN for Hindi, en-IN for English)
            provider: Override default provider
            
        Returns:
            {
                "success": bool,
                "text": str,
                "confidence": float,
                "provider": str,
                "language": str,
                "error": Optional[str]
            }
        """
        provider = provider or self.provider
        
        try:
            # Convert audio to WAV if needed
            if audio_format != "wav":
                audio_data = await self._convert_to_wav(audio_data, audio_format)
            
            if provider == STTProvider.GOOGLE:
                return await self._transcribe_google(audio_data, language)
            elif provider == STTProvider.BHASHINI:
                return await self._transcribe_bhashini(audio_data, language)
            elif provider == STTProvider.WHISPER:
                return await self._transcribe_whisper(audio_data, language)
            elif provider == STTProvider.MOCK:
                return await self._transcribe_mock(audio_data, language)
            else:
                return {
                    "success": False,
                    "text": "",
                    "confidence": 0.0,
                    "provider": provider,
                    "language": language,
                    "error": f"Unknown STT provider: {provider}"
                }
                
        except Exception as e:
            logger.error(f"STT transcription failed: {e}", exc_info=True)
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "provider": provider,
                "language": language,
                "error": str(e)
            }
    
    async def _convert_to_wav(self, audio_data: bytes, from_format: str) -> bytes:
        """Convert audio to WAV format"""
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=from_format)
            
            # Convert to 16kHz mono for better STT results
            audio = audio.set_frame_rate(16000).set_channels(1)
            
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            return wav_buffer.getvalue()
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise
    
    async def _transcribe_google(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """Transcribe using Google Cloud Speech-to-Text"""
        try:
            from google.cloud import speech
            
            client = speech.SpeechClient()
            
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language,
                enable_automatic_punctuation=True,
                model="default",
                use_enhanced=True if language == "hi-IN" else False
            )
            
            response = client.recognize(config=config, audio=audio)
            
            if not response.results:
                return {
                    "success": False,
                    "text": "",
                    "confidence": 0.0,
                    "provider": "google",
                    "language": language,
                    "error": "No transcription results"
                }
            
            # Get best alternative
            result = response.results[0]
            alternative = result.alternatives[0]
            
            return {
                "success": True,
                "text": alternative.transcript.strip(),
                "confidence": alternative.confidence,
                "provider": "google",
                "language": language,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Google STT failed: {e}", exc_info=True)
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "provider": "google",
                "language": language,
                "error": str(e)
            }
    
    async def _transcribe_bhashini(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """Transcribe using Bhashini API"""
        try:
            # Map language codes
            lang_map = {
                "hi-IN": "hi",
                "en-IN": "en",
                "ta-IN": "ta",
                "te-IN": "te",
                "kn-IN": "kn"
            }
            bhashini_lang = lang_map.get(language, "hi")
            
            # Bhashini API endpoint
            url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.bhashini_api_key}",
                "Content-Type": "application/json"
            }
            
            # Convert audio to base64
            import base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "asr",
                        "config": {
                            "language": {
                                "sourceLanguage": bhashini_lang
                            }
                        }
                    }
                ],
                "inputData": {
                    "audio": [
                        {
                            "audioContent": audio_base64
                        }
                    ]
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                
                if "pipelineResponse" in result and result["pipelineResponse"]:
                    text = result["pipelineResponse"][0]["output"][0]["source"]
                    return {
                        "success": True,
                        "text": text.strip(),
                        "confidence": 0.9,  # Bhashini doesn't provide confidence
                        "provider": "bhashini",
                        "language": language,
                        "error": None
                    }
                
                return {
                    "success": False,
                    "text": "",
                    "confidence": 0.0,
                    "provider": "bhashini",
                    "language": language,
                    "error": "No transcription in response"
                }
                
        except Exception as e:
            logger.error(f"Bhashini STT failed: {e}", exc_info=True)
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "provider": "bhashini",
                "language": language,
                "error": str(e)
            }
    
    async def _transcribe_whisper(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper API"""
        try:
            import openai
            
            openai.api_key = self.openai_api_key
            
            # Map language codes
            lang_map = {
                "hi-IN": "hi",
                "en-IN": "en",
                "ta-IN": "ta",
                "te-IN": "te",
                "kn-IN": "kn"
            }
            whisper_lang = lang_map.get(language, "hi")
            
            # Create audio file object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            # Transcribe
            response = await openai.Audio.atranscribe(
                model="whisper-1",
                file=audio_file,
                language=whisper_lang
            )
            
            return {
                "success": True,
                "text": response["text"].strip(),
                "confidence": 0.95,  # Whisper doesn't provide confidence
                "provider": "whisper",
                "language": language,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Whisper STT failed: {e}", exc_info=True)
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "provider": "whisper",
                "language": language,
                "error": str(e)
            }
    
    async def _transcribe_mock(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """Mock transcription for testing"""
        # Simulate successful transcription
        mock_responses = {
            "hi-IN": "मेरी फसल में कीट लग गए हैं",
            "en-IN": "My crop has pest infestation"
        }
        
        return {
            "success": True,
            "text": mock_responses.get(language, "मेरी फसल में समस्या है"),
            "confidence": 1.0,
            "provider": "mock",
            "language": language,
            "error": None
        }


# Global instance
stt_service = STTService()
