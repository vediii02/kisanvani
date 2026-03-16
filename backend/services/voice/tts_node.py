import asyncio
import base64
import json
import os
from typing import AsyncIterator
from dotenv import load_dotenv

from sarvamai import AsyncSarvamAI, AudioOutput
import websockets
from services.voice.events import VoiceAgentEvent, TTSChunkEvent, BargeInEvent, FillerAudioEvent, AgentEndEvent
from services.voice.logger import setup_logger
from services.config_service import get_platform_config
from services.voice.session_context import get_current_session_id, session_state_manager

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
        self._send_lock = asyncio.Lock()  # Serialize convert() and flush() calls
        self._receive_task = None
        # Ultra-low latency queue — slightly larger to reduce random drops under bursty network
        self.output_queue = asyncio.Queue(maxsize=32)
        self._ignore_audio = False
        self._first_chunk_received = False
        self._real_chunk_event = asyncio.Event() # Refine 12: Event to skip filler if response is fast
        # Bug 2: Track all active send tasks to cancel them ALL on barge-in
        self._send_tasks: list[asyncio.Task] = []
        # Bug 3: Turn ID to prevent race conditions during flushing
        self._turn_id: int = 0
        self._active_turn: int = 0  # Tracking the current turn being synthesized

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
        logger.info("SarvamTTS: receiver loop started")
        try:
            async for message in ws:
                if isinstance(message, AudioOutput):
                    try:
                        sid = get_current_session_id()
                        session_state = session_state_manager.get_state(sid) if sid else None
                        
                        if self._ignore_audio or (session_state and session_state.is_interrupted):
                            continue
                        audio_chunk = base64.b64decode(message.data.audio)
                        if audio_chunk:
                            # Cross-turn filter: only accept audio for the current active turn
                            # Relaxed: allow turn_id or active_turn to match to avoid race synchronization issues
                            if self._active_turn != self._turn_id:
                                logger.debug(
                                    f"SarvamTTS: Dropping chunk for turn imbalance "
                                    f"(active_turn={self._active_turn}, turn_id={self._turn_id})"
                                )
                                continue
                            try:
                                self.output_queue.put_nowait(TTSChunkEvent.create(audio_chunk, turn_id=self._active_turn))
                            except asyncio.QueueFull:
                                logger.warning(
                                    "SarvamTTS: output queue full, dropping audio chunk "
                                    f"(len={len(audio_chunk)})"
                                )
                    except Exception as e:
                        logger.error(f"Raw Decode Error: {e}", exc_info=True)
        except asyncio.CancelledError:
            logger.info("SarvamTTS: receiver loop cancelled")
        except Exception as e:
             logger.error(f"SarvamTTS: Receiver Error: {e}", exc_info=True)
        finally:
             logger.info("SarvamTTS: receiver loop finished.")

    async def send_text(self, text: str, turn_id: int = 0) -> None:
        """Send text to Sarvam for synthesis."""
        if not text or not text.strip():
            return
        
        # Sync both counters so the receiver_loop cross-turn filter allows this audio
        self._active_turn = turn_id
        self._turn_id = turn_id
        try:
            ws = await self._ensure_connection()
            if not ws:
                return
            
            # Re-enable audio reception for this new turn
            self._ignore_audio = False
            
            logger.info(f"SarvamTTS: Sending text for turn {turn_id}: {text}")
            async with self._send_lock:
                await ws.convert(text)
            logger.debug(f"SarvamTTS: convert() completed for turn {turn_id}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"SarvamTTS: Send Error: {e}. Resetting connection.", exc_info=True)
            # Refine 6: Avoid deadlock by setting to None instead of calling close() which acquires lock
            self._ws = None 

    async def flush_tts(self) -> None:
        """Call once after all sentences of a response are sent."""
        captured_turn = self._turn_id
        logger.info(f"SarvamTTS: flush_tts() requested for turn {captured_turn}")
        try:
            ws = await self._ensure_connection()
            if ws:
                async with self._send_lock:
                    await ws.flush()
                logger.info(f"SarvamTTS: ws.flush() completed for turn {captured_turn}")
                # Bug 3: Only reset if still same turn — barge-in increments _turn_id
                if self._turn_id == captured_turn:
                    self._ignore_audio = False
        except Exception as e:
            logger.error(f"SarvamTTS: Flush Error: {e}", exc_info=True)

    async def flush(self):
        """Ignore any pending audio from the server."""
        self._ignore_audio = True
        logger.info("SarvamTTS: TTS Flushed (ignoring incoming audio)")

    async def close(self):
        """Closes the current socket connection safely."""
        async with self._conn_lock:
            if self._receive_task:
                self._receive_task.cancel()
                self._receive_task = None
            if self._ws_context:
                try:
                    # Flush with timeout to prevent hanging if socket is already dead
                    if self._ws:
                        try:
                            await asyncio.wait_for(self._ws.flush(), timeout=2.0)
                        except Exception:
                            pass
                    await self._ws_context.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning("TTS socket close warning: %s", e)
                self._ws = None
                self._ws_context = None
                logger.debug("TTS Connection closed.")

    def clear_queues(self):
        """Root Cause 2: Deep purge of output queue."""
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        logger.info("TTS Output Queue cleared.")

class CartesiaTTS:
    def __init__(self, api_key: str = None, voice_id: str = "faf0731e-dfb9-4cfc-8119-259a79b27e12", language: str = "hi"):
        self.api_key = api_key or os.getenv("CARTESIA_API_KEY")
        self.voice_id = voice_id
        self.language = language
        self.output_queue = asyncio.Queue(maxsize=32)
        
        self._ws = None
        self._conn_lock = asyncio.Lock()
        self._send_lock = asyncio.Lock()
        self._receive_task = None
        self._ignore_audio = False
        
        self._turn_id: int = 0
        self._active_turn: int = 0
        self._send_tasks: list[asyncio.Task] = []
        self._context_id: str = None
        self._first_chunk_received = False
        self._real_chunk_event = asyncio.Event()

    async def _ensure_connection(self):
        async with self._conn_lock:
            # Check if connection exists and is open
            is_open = False
            if self._ws is not None:
                # websockets v14+ uses state, older versions use closed property
                state_name = getattr(self._ws, "state", None)
                if state_name is not None:
                    # state is an Enum like websockets.protocol.State.OPEN
                    is_open = str(state_name) == "State.OPEN" or getattr(state_name, "name", "") == "OPEN"
                else:
                    is_open = not getattr(self._ws, "closed", True)

            if not is_open:
                logger.info("Connecting to Cartesia WebSocket...")
                url = "wss://api.cartesia.ai/tts/websocket"
                headers = {
                    "X-API-Key": self.api_key,
                    "Cartesia-Version": "2024-06-10"
                }
                try:
                    # Use a slightly longer timeout and headers
                    # websockets v14+ uses 'additional_headers' instead of 'extra_headers'
                    self._ws = await websockets.connect(
                        url, 
                        additional_headers=headers,
                        open_timeout=20
                    )
                    logger.info("Cartesia WebSocket connected.")
                    
                    if self._receive_task:
                        self._receive_task.cancel()
                    self._receive_task = asyncio.create_task(self._receiver_loop(self._ws))
                except Exception as e:
                    logger.error(f"Cartesia Connection Failed: {e}", exc_info=True)
                    self._ws = None
                    raise
        return self._ws

    async def _receiver_loop(self, ws):
        logger.info("CartesiaTTS: receiver loop started")
        try:
            async for message_str in ws:
                try:
                    message = json.loads(message_str)
                    msg_type = message.get("type")
                    context_id = message.get("context_id")
                    
                    if msg_type == "chunk":
                        sid = get_current_session_id()
                        session_state = session_state_manager.get_state(sid) if sid else None
                        
                        if self._ignore_audio or (session_state and session_state.is_interrupted):
                            continue
                            
                        data = message.get("data")
                        if data:
                            audio_chunk = base64.b64decode(data)
                            if str(self._active_turn) != context_id:
                                logger.debug(f"CartesiaTTS: Dropping chunk for stale context {context_id} (active_turn={self._active_turn})")
                                continue
                                    
                            self.output_queue.put_nowait(TTSChunkEvent.create(audio_chunk, turn_id=self._active_turn))
                    
                    elif msg_type == "done":
                        logger.info(f"CartesiaTTS: Generation done for context {context_id}")
                    
                    elif msg_type == "error":
                        logger.error(f"CartesiaTTS Error message: {message.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Cartesia Message Parse Error: {e}", exc_info=True)
                    
        except asyncio.CancelledError:
            logger.info("CartesiaTTS: receiver loop cancelled")
        except Exception as e:
            logger.error(f"Cartesia Receiver Loop Error: {e}", exc_info=True)
        finally:
            logger.info("CartesiaTTS: receiver loop finished")
            # If this was the current websocket, clear it so we re-ensure on next send
            if self._ws == ws:
                self._ws = None

    async def send_text(self, text: str, turn_id: int = 0) -> None:
        if not text or not text.strip():
            return
            
        self._active_turn = turn_id
        self._turn_id = turn_id
        self._context_id = str(turn_id)
        
        try:
            ws = await self._ensure_connection()
            if not ws:
                return
                
            self._ignore_audio = False
            
            payload = {
                "model_id": "sonic-multilingual",
                "transcript": text,
                "voice": {
                    "mode": "id",
                    "id": self.voice_id
                },
                "language": self.language,
                "context_id": self._context_id,
                "output_format": {
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": 8000
                },
                "continue": True
            }
            
            logger.info(f"CartesiaTTS: Sending text for turn {turn_id}: {text[:50]}...")
            async with self._send_lock:
                await ws.send(json.dumps(payload))
                
        except Exception as e:
            logger.error(f"Cartesia Send Error: {e}", exc_info=True)
            self._ws = None

    async def flush_tts(self) -> None:
        captured_turn = self._turn_id
        logger.info(f"CartesiaTTS: flush_tts() for turn {captured_turn}")
        try:
            ws = await self._ensure_connection()
            if ws:
                payload = {
                    "model_id": "sonic-multilingual",
                    "voice": {
                        "mode": "id",
                        "id": self.voice_id
                    },
                    "language": self.language,
                    "context_id": str(captured_turn),
                    "transcript": "",
                    "continue": False,
                    "output_format": {
                        "container": "raw",
                        "encoding": "pcm_s16le",
                        "sample_rate": 8000
                    },
                }
                async with self._send_lock:
                    await ws.send(json.dumps(payload))
        except Exception as e:
            logger.error(f"Cartesia Flush Error: {e}", exc_info=True)

    async def flush(self):
        self._ignore_audio = True
        logger.info("CartesiaTTS: TTS Flushed (ignoring audio)")

    async def close(self):
        async with self._conn_lock:
            if self._receive_task:
                self._receive_task.cancel()
                self._receive_task = None
            if self._ws:
                try:
                    await self._ws.close()
                except Exception as e:
                    logger.warning(f"Cartesia close warning: {e}")
                self._ws = None

    def clear_queues(self):
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        logger.info("CartesiaTTS: Output Queue cleared.")

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
        self.output_queue = asyncio.Queue(maxsize=50) # Refine 4: Bound queue
        self._ignore_audio = False
        self._first_chunk_received = False
        self._real_chunk_event = asyncio.Event()
        self._send_tasks: list[asyncio.Task] = []
        self._turn_id: int = 0
        self._active_turn: int = 0

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

    async def flush(self):
        self._ignore_audio = True

    async def flush_tts(self) -> None:
        """Required for API compatibility with tts_stream."""
        pass

    def clear_queues(self):
        """Required for API compatibility with tts_stream."""
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        logger.info("GoogleTTS: Output Queue cleared.")

    async def close(self):
        logger.info("Google TTS Connection closed.")


async def tts_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
    tts_provider: str | None = None,
) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: Voice Events → Voice Events (with Audio)
    Simplified logic to avoid event duplication and deadlocks.
    """
    config = await get_platform_config()
    if tts_provider is None:
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
    elif tts_provider == "cartesia":
        # Use Sonic Multilingual for Cartesia
        # Voice: Indian Female (3b554273-4299-48b9-9aaf-eefd438e3941)
        cartesia_voice = os.getenv("CARTESIA_VOICE_ID", "3b554273-4299-48b9-9aaf-eefd438e3941")
        cartesia_lang = provider_lang.split('-')[0] # 'hi-IN' -> 'hi'
        logger.info(f"Using Cartesia TTS ({cartesia_lang} - Voice: {cartesia_voice})")
        tts = CartesiaTTS(voice_id=cartesia_voice, language=cartesia_lang)
        asyncio.create_task(tts._ensure_connection())
    else:
        logger.info(f"Using Sarvam TTS ({provider_lang} - Speaker: {sarvam_speaker})")
        tts = SarvamTTS(language_code=provider_lang, speaker=sarvam_speaker)
        # Pre-warm connection immediately
        asyncio.create_task(tts._ensure_connection())

    async def upstream_listener():
        """Consumes events from Agent/Upstream and puts them in output queue."""
        try:
            async for event in event_stream:
                # Refine 7: Reset first chunk flag on new turn (barge-in or new STT)
                if event.type in ["barge_in", "stt_output", "call_started"]:
                    if hasattr(tts, '_first_chunk_received'):
                        tts._first_chunk_received = False
                    if hasattr(tts, '_real_chunk_event'):
                        tts._real_chunk_event.clear() # Clear event for new turn

                # 1. Put the original event into the output queue (Passthrough)
                # Skip barge_in here — it's re-queued after cleanup in the handler below
                if event.type != "barge_in":
                    try:
                        tts.output_queue.put_nowait(event)
                    except asyncio.QueueFull:
                        logger.warning(f"TTS output queue full, dropping {event.type}")

                # 2. Handle specific events
                if event.type == "filler_audio":
                    async def _play_filler_with_delay():
                        try:
                            # Wait up to 250ms for the first chunk to arrive from Groq/LLM
                            await asyncio.wait_for(tts._real_chunk_event.wait(), timeout=0.25)
                            logger.info("Real response arrived, skipping filler.")
                        except asyncio.TimeoutError:
                            sid = get_current_session_id()
                            state = session_state_manager.get_state(sid) if sid else None
                            if not tts._ignore_audio and not (state and state.is_interrupted):
                                logger.info("Playing filler audio to mask latency.")
                                await tts.send_text("जी, ")
                        except Exception as e:
                            logger.error(f"Error in filler delay task: {e}")

                    task = asyncio.create_task(_play_filler_with_delay())
                    tts._send_tasks.append(task)
                    continue

                if event.type == "barge_in":
                    logger.info("Barge-in: Full cleanup sequence starting.")

                    sid = get_current_session_id()
                    state = session_state_manager.get_state(sid) if sid else None

                    # Safety: ensure interrupt state is set (idempotent if already set by STT)
                    if state:
                        state.interrupt()

                    # 1. Stop receiving audio from Sarvam
                    await tts.flush()

                    # 2. Purge all queued audio chunks
                    tts.clear_queues()

                    # 3. Cancel all in-flight synthesis tasks
                    for task in tts._send_tasks:
                        if not task.done():
                            task.cancel()
                    tts._send_tasks.clear()

                    # 4. IMPORTANT: Kill the websocket so Sarvam stops streaming
                    try:
                        async with asyncio.timeout(2.0):
                            await tts.close()
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        logger.warning("TTS close timed out during barge-in")

                    # 5. Advance turn id so receiver cross-turn filter rejects old audio
                    # DO NOT set _active_turn here — leave it stale so
                    # _active_turn != _turn_id triggers the filter
                    tts._turn_id += 1

                    # Pass through the barge_in event so server.py sees it
                    try:
                        tts.output_queue.put_nowait(event)
                    except asyncio.QueueFull:
                        pass
                    continue

                if event.type == "agent_end":
                    # Fix 40% drop rate: wait for all in-flight text to be sent BEFORE flushing
                    async def _flush_after_sends(captured_turn: int):
                        logger.info(f"TTS Stream: _flush_after_sends started for turn {captured_turn} "
                                    f"(pending_tasks={len(tts._send_tasks)})")
                        if tts._send_tasks:
                            await asyncio.gather(*tts._send_tasks, return_exceptions=True)
                        # Only flush if we are still on the same turn; otherwise this is stale
                        if getattr(tts, "_turn_id", None) == captured_turn:
                            await tts.flush_tts()
                        else:
                            logger.info(
                                "TTS Stream: Skipping flush_tts for stale turn "
                                f"{captured_turn} (current_turn={getattr(tts, '_turn_id', None)})"
                            )

                    current_turn = getattr(event, "turn_id", getattr(tts, "_turn_id", 0))
                    asyncio.create_task(_flush_after_sends(current_turn))
                    continue

                if event.type == "agent_chunk":
                    # Process current chunk
                    current_turn = getattr(event, 'turn_id', 0)
                    if not getattr(tts, "_first_chunk_received", False):
                        logger.info(f"First real chunk received from LLM for turn {current_turn}. Provider: {tts_provider}")
                        if hasattr(tts, "_first_chunk_received"):
                            tts._first_chunk_received = True
                        if hasattr(tts, '_real_chunk_event'):
                            tts._real_chunk_event.set() # Set event to unblock any waiting filler logic
                        # START HEARING: Now that we have the first chunk of the NEW response
                        tts._ignore_audio = False
                    
                    # Manage send tasks list
                    task = asyncio.create_task(tts.send_text(event.text, turn_id=current_turn))
                    tts._send_tasks.append(task)
                    # Keep list clean
                    tts._send_tasks = [t for t in tts._send_tasks if not t.done()]
                    continue
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
            # CRITICAL: Drop any stale audio chunks if the turn was flushed/interrupted
            sid = get_current_session_id()
            state = session_state_manager.get_state(sid) if sid else None
            if event.type == "tts_chunk":
                if getattr(tts, "_ignore_audio", False) or (state and state.is_interrupted):
                    logger.info(f"TTS: Dropping audio chunk (ignore={getattr(tts, '_ignore_audio', False)}, interrupted={state and state.is_interrupted})")
                    continue
                logger.info(f"TTS: Yielding audio chunk (len={len(event.audio or b'')})")
            yield event
    finally:
        await tts.close()
