import asyncio
import base64
import os
import sys
import json
from typing import AsyncIterator
from dotenv import load_dotenv

from sarvamai import AsyncSarvamAI
import websockets
import webrtcvad

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.voice.events import VoiceAgentEvent, STTChunkEvent, STTOutputEvent, STTInterimEvent, BargeInEvent, CallStartedEvent
from services.voice.logger import setup_logger
from services.config_service import get_platform_config

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
            self.barge_in_threshold = int(os.getenv("BARGE_IN_THRESHOLD", "10"))
        except ValueError:
            self.barge_in_threshold = 10
            
        # VAD Initialize (Mode 1: light, 2: moderate, 3: aggressive)
        self.vad = webrtcvad.Vad(2)
        self._audio_buffer = bytearray()
        # VAD requires frames of 10, 20, or 30ms.
        # At 8000Hz, 30ms = 240 samples = 480 bytes (16-bit PCM)
        self._vad_frame_size = 480 
        
        self._closed = False
        self._chunk_log_counter = 0
        self._vad_log_counter = 0

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
                logger.info(f"Connecting to SarvamAI (Rate: {self.sample_rate})...")
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
                except Exception as e:
                    logger.error(f"Connection Failed: {e}", exc_info=True)
                    self._ws = None # Ensure it's None on failure
                    raise # Re-raise to let the caller handle it
        return self._ws

    async def send_audio(self, audio_chunk: bytes) -> None:
        if not audio_chunk:
            return
        try:
            ws = await self._ensure_connection()
            if not ws:
                return
            
            # append to buffer
            self._chunk_log_counter += 1
            if self._chunk_log_counter % 20 == 0:
                logger.debug(f"Received audio chunk: len={len(audio_chunk)}")
                
            self._audio_buffer.extend(audio_chunk)
            
            # Process buffer in 30ms frames
            while len(self._audio_buffer) >= self._vad_frame_size:
                frame = bytes(self._audio_buffer[:self._vad_frame_size])
                self._audio_buffer = self._audio_buffer[self._vad_frame_size:]
                
                # Check VAD
                is_speech = self.vad.is_speech(frame, self.sample_rate)
                
                # Debug logging - only log every 10 frames to avoid flooding
                if not hasattr(self, "_vad_log_counter"): self._vad_log_counter = 0
                self._vad_log_counter += 1
                if self._vad_log_counter % 20 == 0:
                    logger.debug(f"VAD check: is_speech={is_speech}, buffer_len={len(self._audio_buffer)}")

                if is_speech:
                    b64_audio = base64.b64encode(frame).decode("utf-8")
                    payload = {
                        "audio": {
                            "data": b64_audio,
                            "encoding": "audio/wav", # Mandated by Sarvam server
                            "sample_rate": self.sample_rate
                        }
                    }
                    await self._ws._websocket.send(json.dumps(payload))
                # else: ignore noise frames locally
                
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
                        # Sarvam STT receiver loop
                        # Slightly under 1s to keep end-to-end TTFB low while
                        # still allowing natural short pauses.
                        message = await asyncio.wait_for(ws.recv(), timeout=0.9)

                        data = getattr(message, "data", None)
                        if data and hasattr(data, "transcript"):
                            transcript = data.transcript
                            if not transcript or transcript == last_yielded_transcript:
                                continue

                            last_yielded_transcript = transcript
                            pending_transcript = transcript
                            is_final_msg = getattr(data, "is_final", None)
                            if is_final_msg is not None:
                                is_final = bool(is_final_msg)
                            else:
                                # Fallback to punctuation detection
                                is_final = any(p in transcript for p in ["।", ".", "?", "!"])

                            logger.info(f"STT Result: {transcript} (final={is_final})")

                            # Only yield BargeIn if intent is detected (at least 2 words or long enough)
                            words = transcript.strip().split()
                            if len(words) >= 2 or len(transcript) >= self.barge_in_threshold:
                                yield BargeInEvent.create()

                            if is_final:
                                yield STTOutputEvent.create(transcript=transcript)
                                pending_transcript = ""  # Cleared because it was final
                            else:
                                # STTChunkEvent: always yield for UI/Exotel feedback
                                yield STTChunkEvent.create(transcript=transcript)
                                
                                # STTInterimEvent: yield only for speculative LLM triggering
                                # We want to give the LLM a head start once the user has said a meaningful amount
                                if len(words) >= 3:
                                    yield STTInterimEvent.create(transcript=transcript)
                        else:
                            logger.info(f"Unknown Msg: {message}")

                    except asyncio.TimeoutError:
                        # User stopped speaking for ~0.9s. If we have pending text, make it final
                        if pending_transcript:
                            logger.info(f"Silence timeout (0.9s). Flushing as final: {pending_transcript}")
                            yield STTOutputEvent.create(transcript=pending_transcript)
                            pending_transcript = ""
                            last_yielded_transcript = ""  # Reset so next utterance isn't skipped if identical
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
    logger.info("STT_STREAM: ENTRY")
    # Yield CallStartedEvent IMMEDIATELY to kick off the pipeline chain
    ev = CallStartedEvent.create()
    logger.info(f"STT_STREAM: YIELDING {ev.type}")
    yield ev

    config = await get_platform_config()
    stt_provider = config.get("stt_provider", "sarvam")
    lang_code = config.get("default_language", "hi")
    
    # Map short codes to full BCP-47 tags
    lang_map = {
        "hi": "hi-IN",
        "en": "en-IN",
        "pa": "pa-IN",
        "mr": "mr-IN"
    }
    full_lang_code = lang_map.get(lang_code, "hi-IN")

    if stt_provider == "google":
        logger.info(f"Using Google STT with language: {full_lang_code}")
        from google.cloud import speech

        client = speech.SpeechAsyncClient()
        config_req = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=8000,
            language_code=full_lang_code,
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
                if len(words) >= 2 or len(transcript) >= barge_in_threshold:
                    yield BargeInEvent.create()
                
                if is_final:
                    yield STTOutputEvent.create(transcript=transcript)
                else:
                    yield STTChunkEvent.create(transcript=transcript)

        except Exception as e:
            logger.error(f"Google STT Error: {e}", exc_info=True)

    else:
        logger.info(f"Using Sarvam STT with language: {full_lang_code}")
        stt = SarvamSTT(sample_rate=8000, language_code=full_lang_code)
        
        async def send_audio_task():
            try:
                async for chunk in audio_stream:
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
