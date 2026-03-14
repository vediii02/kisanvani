import asyncio
import base64
import os
from typing import AsyncIterator
from dotenv import load_dotenv

from sarvamai import AsyncSarvamAI, AudioOutput
from services.voice.events import VoiceAgentEvent, TTSChunkEvent, BargeInEvent, FillerAudioEvent
from services.voice.logger import setup_logger
from services.config_service import get_platform_config

logger = setup_logger("tts_node")

load_dotenv()

class SarvamTTS:
    def __init__(self, api_key: str = None, language_code: str = "hi-IN", speaker: str = "pooja"):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY")
        self.language_code = language_code
        self.speaker = speaker
        self.client = AsyncSarvamAI(api_subscription_key=self.api_key)
        self._ws_context = None
        self._ws = None
        self._conn_lock = asyncio.Lock()
        self._receive_task = None
        self.output_queue = asyncio.Queue()

    async def _ensure_connection(self):
        async with self._conn_lock:
            if self._ws is None:
                logger.info("Connecting to SarvamAI...")
                try:
                    self._ws_context = self.client.text_to_speech_streaming.connect(model="bulbul:v3")
                    self._ws = await self._ws_context.__aenter__()
                    # Configure the TTS connection
                    await self._ws.configure(
                        target_language_code=self.language_code,
                        speaker=self.speaker,
                        speech_sample_rate=8000,
                        output_audio_codec="linear16"
                    )
                    logger.info("Connected.")
                    # Start receiver task for this new connection
                    if self._receive_task:
                        self._receive_task.cancel()
                    self._receive_task = asyncio.create_task(self._receiver_loop(self._ws))
                except Exception as e:
                    logger.error(f"Connection Failed: {e}", exc_info=True)
                    self._ws = None # Ensure it's None on failure
                    raise # Let caller handle the exception
        return self._ws

    async def _receiver_loop(self, ws):
        """Internal loop to pump audio chunks into the output queue."""
        try:
            async for message in ws:
                if isinstance(message, AudioOutput):
                    try:
                        audio_chunk = base64.b64decode(message.data.audio)
                        if audio_chunk:
                            await self.output_queue.put(TTSChunkEvent.create(audio_chunk))
                    except Exception as e:
                        logger.error(f"Raw Decode Error: {e}", exc_info=True)
        except asyncio.CancelledError:
            pass
        except Exception as e:
             logger.error(f"Receiver Error: {e}", exc_info=True)
        finally:
             logger.info("Receiver loop finished.")

    async def send_text(self, text: str) -> None:
        """Send text to Sarvam for synthesis."""
        if not text or not text.strip():
            return
        try:
            ws = await self._ensure_connection()
            if not ws:
                return
                
            logger.info(f"Sending: {text}")
            await ws.convert(text)
            await ws.flush()
        except Exception as e:
            logger.error(f"Send Error: {e}. Resetting connection.", exc_info=True)
            await self.close()

    async def close(self):
        async with self._conn_lock:
            if self._receive_task:
                self._receive_task.cancel()
                self._receive_task = None
            if self._ws_context:
                try:
                    await self._ws_context.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning("TTS socket close warning: %s", e)
                self._ws = None
                self._ws_context = None
                logger.info("Connection closed.")

class GoogleTTS:
    def __init__(self, language_code: str = "hi-IN"):
        from google.cloud import texttospeech
        self._tts_module = texttospeech
        self.client = texttospeech.TextToSpeechAsyncClient()
        
        # Use Standard voice for non-Hindi as fallback if Wavenet-A doesn't exist
        voice_name = f"{language_code}-Wavenet-A" if language_code == "hi-IN" else f"{language_code}-Standard-A"
        
        self.voice = texttospeech.VoiceSelectionParams(
            language_code=language_code, name=voice_name
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=8000
        )
        self.output_queue = asyncio.Queue()

    async def _receiver_loop(self):
        pass # Google TTS is not streaming receive like Sarvam, we handle it in send_text

    async def send_text(self, text: str) -> None:
        """Send text to Google for synthesis."""
        if not text or not text.strip():
            return
        try:
            logger.info(f"Sending to Google TTS: {text}")
            synthesis_input = self._tts_module.SynthesisInput(text=text)
            response = await self.client.synthesize_speech(
                input=synthesis_input, voice=self.voice, audio_config=self.audio_config
            )
            # The response.audio_content contains the WAV header as well if LINEAR16 is used,
            # but for raw PCM we just need the raw audio bytes. LINEAR16 typically includes a 44-byte WAV header.
            # We strip the first 44 bytes to get raw PCM data.
            audio_chunk = response.audio_content[44:] if len(response.audio_content) > 44 else response.audio_content
            if audio_chunk:
                await self.output_queue.put(TTSChunkEvent.create(audio_chunk))
        except Exception as e:
            logger.error(f"Google TTS Send Error: {e}", exc_info=True)

    async def close(self):
        logger.info("Google TTS Connection closed.")


async def tts_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: Voice Events → Voice Events (with Audio)
    Simplified logic to avoid event duplication and deadlocks.
    """
    config = await get_platform_config()
    tts_provider = config.get("tts_provider", "sarvam")
    default_lang = config.get("default_language", "hi")
    
    provider_lang = {
        "hi": "hi-IN",
        "en": "en-IN",
        "pa": "pa-IN",
        "mr": "mr-IN"
    }.get(default_lang, "hi-IN")
    
    # Map languages to the best female Sarvam TTS voices to preserve the "KisanVani Krishi Sahayak" persona
    sarvam_speaker_map = {
        "hi-IN": "pooja",    # Empathetic Hindi female
        "pa-IN": "simran",   # Warm Punjabi/conversational female
        "mr-IN": "kavya",    # Clear everyday conversational female
        "en-IN": "shreya"    # Authoritative English female
    }
    sarvam_speaker = sarvam_speaker_map.get(provider_lang, "pooja")
    
    if tts_provider == "google":
        logger.info(f"Using Google TTS ({provider_lang})")
        tts = GoogleTTS(language_code=provider_lang)
    else:
        logger.info(f"Using Sarvam TTS ({provider_lang} - Speaker: {sarvam_speaker})")
        tts = SarvamTTS(language_code=provider_lang, speaker=sarvam_speaker)

    async def upstream_listener():
        """Consumes events from Agent/Upstream and puts them in output queue."""
        try:
            async for event in event_stream:
                # 1. Put the original event into the output queue (Passthrough)
                await tts.output_queue.put(event)

                # 2. Handle specific events
                if event.type == "filler_audio":
                    logger.info("Playing filler audio to mask latency.")
                    # Fast-path TTS for instant audio feedback
                    await tts.send_text("जी, ")
                    continue

                if event.type == "barge_in":
                    logger.info("Interruption detected. Signaling TTS reset.")
                    await tts.close()
                    
                    # CASCADING FLUSH: Drain existing chunks from the queue
                    while not tts.output_queue.empty():
                        try:
                            tts.output_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                    
                    await tts.output_queue.put(event) # Passthrough the barge_in event
                    continue

                if event.type == "agent_chunk":
                    # Start synthesis for the new chunk
                    await tts.send_text(event.text)
        finally:
            # Signal end of stream
            await tts.output_queue.put(None)

    # Start the upstream listener in the background
    asyncio.create_task(upstream_listener())

    try:
        # Yield everything from the output queue
        while True:
            event = await tts.output_queue.get()
            if event is None:
                break
            yield event
    finally:
        await tts.close()
