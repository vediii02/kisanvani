import asyncio
import base64
import os
import sys
import json
from typing import AsyncIterator
from dotenv import load_dotenv

from sarvamai import AsyncSarvamAI
import websockets

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.voice.events import VoiceAgentEvent, STTChunkEvent, STTOutputEvent, BargeInEvent, CallStartedEvent
from services.voice.logger import setup_logger
from services.config_service import get_platform_config
from services.voice.session_context import get_current_session_id, session_state_manager

logger = setup_logger("stt_node")

load_dotenv()

class SarvamSTT:
    def __init__(self, sample_rate: int = 8000, language_code: str = "hi-IN"):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.sample_rate = sample_rate
        self.language_code = language_code
        self.client = AsyncSarvamAI(api_subscription_key=self.api_key)
        self._ws_context = None
        self._ws = None
        self._conn_lock = asyncio.Lock()
        self._ping_task = None
        # Threshold for barge-in sensitivity (min characters)
        try:
            self.barge_in_threshold = int(os.getenv("BARGE_IN_THRESHOLD", "15"))
        except ValueError:
            self.barge_in_threshold = 10
        self._closed = False
        self._barge_in_sent = False # Fix 1: Debounce barge-in emissions

    async def _mark_disconnected(self):
        async with self._conn_lock:
            self._ws = None
            self._ws_context = None

    async def _ping_loop(self):
        try:
            while True:
                await asyncio.sleep(15)
                async with self._conn_lock:
                    if self._ws and hasattr(self._ws, "_websocket"):
                        await self._ws._websocket.ping()
        except (asyncio.CancelledError, Exception):
            pass

    async def _ensure_connection(self):
        async with self._conn_lock:
            ws_closed = False
            if self._ws is not None and hasattr(self._ws, "_websocket"):
                ws_closed = getattr(self._ws._websocket, "closed", False)

            if self._ws is None or ws_closed:
                # Fix 3: Exponential backoff for reconnections
                retry_delay = 0.5
                max_retries = 5
                for attempt in range(max_retries):
                    logger.info(f"Connecting to SarvamAI (Rate: {self.sample_rate}, Attempt {attempt+1})...")
                    try:
                        if self._ping_task:
                            self._ping_task.cancel()
                            self._ping_task = None
                        self._ws_context = self.client.speech_to_text_streaming.connect(
                            language_code=self.language_code,
                            sample_rate=str(self.sample_rate),
                            input_audio_codec="pcm_s16le"
                        )
                        self._ws = await self._ws_context.__aenter__()
                        logger.info("Connected.")
                        self._ping_task = asyncio.create_task(self._ping_loop())
                        break 
                    except Exception as e:
                        logger.error(f"Connection Attempt {attempt+1} Failed: {e}")
                        if attempt == max_retries - 1:
                            self._ws = None
                            raise
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 5.0)
        return self._ws

    async def send_audio(self, audio_chunk: bytes) -> None:
        if not audio_chunk:
            return
        try:
            ws = await self._ensure_connection()
            if not ws:
                return
            
            b64_audio = base64.b64encode(audio_chunk).decode("utf-8")
            payload = {
                "audio": {
                    "data": b64_audio,
                    "encoding": "audio/wav", # Mandated by Sarvam server
                    "sample_rate": self.sample_rate
                }
            }
            # Send raw JSON to bypass Pydantic validation
            await self._ws._websocket.send(json.dumps(payload))
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Sarvam send socket closed ({e.code}); will reconnect.")
            await self._mark_disconnected()
        except Exception as e:
            logger.error(f"Send Error: {e}", exc_info=True)
            # Optionally trigger reconnect logic here if needed for long-running sessions

    async def receive_events(self) -> AsyncIterator[VoiceAgentEvent]:
        last_yielded_transcript = ""
        pending_transcript = ""

        while not self._closed:
            try:
                ws = await self._ensure_connection()
                if not ws:
                    await asyncio.sleep(0.5)
                    continue

                while not self._closed:
                    try:
                        # Increased silence flush timeout (0.6s) for more natural speech finalization
                        message = await asyncio.wait_for(ws.recv(), timeout=0.6)

                        data = getattr(message, "data", None)
                        if data and hasattr(data, "transcript"):
                            transcript = data.transcript
                            if not transcript or transcript == last_yielded_transcript:
                                continue

                            last_yielded_transcript = transcript
                            pending_transcript = transcript
                            is_final = any(p in transcript for p in ["।", ".", "?", "!"])

                            logger.info(f"Raw: {transcript} (final={is_final})")

                            sid = get_current_session_id()
                            state = session_state_manager.get_state(sid) if sid else None

                            # Only yield BargeIn if intent is detected (at least 1 word or long enough)
                            # CRITICAL: Do NOT gate on state.interrupt() return value!
                            # VAD in server.py may have already called interrupt(), making it return False.
                            # If we skip the BargeInEvent, TTS never gets the cleanup signal → audio overlap.
                            words = transcript.strip().split()
                            if (len(words) >= 2 or len(transcript) >= self.barge_in_threshold) and not self._barge_in_sent:
                                self._barge_in_sent = True
                                # Set interrupt state (may already be set by VAD — that's OK)
                                if state:
                                    state.interrupt()
                                yield BargeInEvent.create()

                            if is_final:
                                # Reset interrupt so the next AI response is allowed to speak
                                if state:
                                    state.reset_interrupt()
                                yield STTOutputEvent.create(transcript=transcript)
                                pending_transcript = ""  # Cleared because it was final
                                self._barge_in_sent = False # Reset for next utterance
                            else:
                                yield STTChunkEvent.create(transcript=transcript)
                        else:
                            logger.info(f"Unknown Msg: {message}")

                    except asyncio.TimeoutError:
                        # User stopped speaking for 0.05s (very sensitive)
                        # If a barge-in was sent, reset it so next speech works
                        if self._barge_in_sent:
                            logger.info("Silence timeout after barge-in. Resetting interrupt.")
                            sid = get_current_session_id()
                            state = session_state_manager.get_state(sid) if sid else None
                            if state:
                                state.reset_interrupt()
                            self._barge_in_sent = False

                        # If we have pending text, make it final
                        if pending_transcript:
                            logger.info(f"Silence timeout. Flushing as final: {pending_transcript}")
                            # Reset interrupt so the next AI response is allowed to speak
                            sid = get_current_session_id()
                            state = session_state_manager.get_state(sid) if sid else None
                            if state:
                                state.reset_interrupt()
                            yield STTOutputEvent.create(transcript=pending_transcript)
                            pending_transcript = ""
                            last_yielded_transcript = ""  # Reset so next utterance isn't skipped if identical
                            self._barge_in_sent = False # Reset on flush
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.warning(f"Sarvam receive socket closed ({e.code}); reconnecting.")
                        await self._mark_disconnected()
                        break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Receiver Loop Error: {e}", exc_info=True)
                await asyncio.sleep(0.5)

    async def close(self):
        self._closed = True
        async with self._conn_lock:
            if self._ping_task:
                self._ping_task.cancel()
                self._ping_task = None
            if self._ws_context:
                try:
                    await self._ws_context.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning("STT socket close warning: %s", e)
                self._ws = None
                self._ws_context = None
                logger.info("Connection closed.")

async def stt_stream(
    audio_stream: AsyncIterator[bytes],
) -> AsyncIterator[VoiceAgentEvent]:
    # Yield CallStartedEvent IMMEDIATELY to kick off the pipeline chain
    # Without this, agent_stream never starts because silence produces no STT events
    from services.voice.session_context import get_current_session_id
    sid = get_current_session_id()
    yield CallStartedEvent.create(session_id=sid)

    config = await get_platform_config()
    stt_provider = config.get("stt_provider", "sarvam")
    default_lang = config.get("default_language", "hi")
    
    provider_lang = {
        "hi": "hi-IN",
        "en": "en-IN",
        "pa": "pa-IN",
        "mr": "mr-IN"
    }.get(default_lang, "hi-IN")

    if stt_provider == "google":
        logger.info(f"Using Google STT ({provider_lang})")
        from google.cloud import speech

        client = speech.SpeechAsyncClient()
        config_req = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=8000,
            language_code=provider_lang,
            enable_automatic_punctuation=True,
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config_req, interim_results=True
        )

        # We must bridge the async generator `audio_stream` to what Google expects
        async def request_generator():
            async for chunk in audio_stream:
                if chunk:
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
        
        try:
            responses = await client.streaming_recognize(
                requests=request_generator(),
                config=streaming_config,
            )
            
            barge_in_threshold = int(os.getenv("BARGE_IN_THRESHOLD", "10"))
            google_barge_in_sent = False
            
            async for response in responses:
                if not response.results:
                    continue
                result = response.results[0]
                if not result.alternatives:
                    continue
                
                transcript = result.alternatives[0].transcript
                is_final = result.is_final
                
                logger.info(f"Google STT Raw: {transcript} (final={is_final})")
                
                words = transcript.strip().split()
                if (len(words) >= 1 or len(transcript) >= barge_in_threshold) and not google_barge_in_sent:
                    google_barge_in_sent = True
                    if state:
                        state.interrupt()
                    yield BargeInEvent.create()
                
                if is_final:
                    if state:
                        state.reset_interrupt()
                    yield STTOutputEvent.create(transcript=transcript)
                    google_barge_in_sent = False
                else:
                    yield STTChunkEvent.create(transcript=transcript)

        except Exception as e:
            logger.error(f"Google STT Error: {e}", exc_info=True)

    else:
        logger.info(f"Using Sarvam STT ({provider_lang})")
        stt = SarvamSTT(sample_rate=8000, language_code=provider_lang)
        
        async def send_audio_task():
            try:
                async for chunk in audio_stream:
                    logger.info(f"STT: Received {len(chunk)} bytes from simulator")
                    await stt.send_audio(chunk)
            except Exception as e:
                logger.error(f"Task Error: {e}", exc_info=True)
            finally:
                await stt.close()

        sender = asyncio.create_task(send_audio_task())
        
        try:
            async for event in stt.receive_events():
                yield event
        finally:
            sender.cancel()
            await stt.close()
