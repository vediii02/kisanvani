import asyncio
import re
import time
from typing import AsyncIterator
from uuid import uuid4

from langchain_core.messages import HumanMessage
from services.voice.events import VoiceAgentEvent, AgentChunkEvent, HangupEvent
from services.voice.llm import get_agent_executor
from services.voice.logger import setup_logger
from services.voice.session_context import get_current_organisation_id, get_current_company_id, get_current_session_id

logger = setup_logger("agent_node")

# How many seconds to ignore barge-in after starting an AI response
BARGE_IN_GRACE_PERIOD = 0.4


async def agent_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: STT Events → Agent Response Events

    Handles:
    - Auto-greeting on call start (sends __CALL_STARTED__ to agent)
    - Multi-turn conversation with memory
    - Barge-in (cancel current AI response) with grace period
    - Sentence-level chunking for TTS
    """
    thread_id = get_current_session_id() or str(uuid4())
    output_queue: asyncio.Queue = asyncio.Queue()
    
    # Active response management
    current_ai_task: asyncio.Task | None = None
    ai_response_start_time: float = 0.0
    
    # Speculative execution state
    speculative_task: asyncio.Task | None = None
    speculative_text: str = ""
    promotion_event: asyncio.Event = asyncio.Event() 
    
    session_org_id = get_current_organisation_id()
    session_comp_id = get_current_company_id()
    session_agent_executor = await get_agent_executor(session_org_id, session_comp_id)
    logger.info("Agent session started: org_id=%s, company_id=%s, thread=%s", session_org_id, session_comp_id, thread_id[:8])

    async def generate_ai_response(text: str, speculative: bool = False):
        """Stream LLM response into the shared output queue, chunked by sentence."""
        nonlocal thread_id
        # ... (rest of the logic updated above in other chunks)
        ttfb_logged = False
        try:
            stream = session_agent_executor.astream(
                {"messages": [HumanMessage(content=text)]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            )
            current_sentence = ""
            async for chunk, metadata in stream:
                # StateGraph can emit raw strings or dicts
                if isinstance(chunk, str) or isinstance(chunk, dict):
                    continue
                    
                message = chunk
                
                # Only listen to messages from our actual speech nodes
                valid_nodes = ["greeting", "profiling", "diagnostic", "advisory"]
                if not metadata or metadata.get("langgraph_node") not in valid_nodes:
                    continue

                # AIMessageChunk has .type == 'AIMessageChunk', not 'ai'
                is_ai = hasattr(message, 'content') and 'ai' in message.type.lower()
                
                # Deduplicate final full message emissions
                if getattr(message, "chunk", None) == False:
                    continue

                # Skip tool calls/responses
                is_tool = getattr(message, 'tool_calls', None) or getattr(message, 'tool_call_chunks', None)
                
                if is_ai and message.content and not is_tool:
                    chunk = message.content
                    if isinstance(chunk, list):
                        chunk = "".join([
                            c.get("text", "") for c in chunk
                            if isinstance(c, dict) and "text" in c
                        ])

                    # Safety: strip raw function call text that some models output as plain text
                    chunk = re.sub(r'<function=\w+>.*?</function>', '', chunk, flags=re.DOTALL)
                    chunk = re.sub(r'<function=\w+>.*', '', chunk, flags=re.DOTALL)
                    if not chunk.strip():
                        continue

                    for char in chunk:
                        current_sentence += char
                        
                        # Detect if this is the first chunk ever sent for this AI response
                        is_first_chunk_of_response = not ttfb_logged
                        
                        # Sentence boundaries (best for naturalness and voice quality)
                        # Avoid aggressive sub-sentence splitting to prevent "voice breaking"
                        should_split = char in ['.', '!', '?', '।', '\n']
                            
                        if should_split:
                            sentence = current_sentence.strip()
                            if sentence:
                                if not ttfb_logged:
                                    ttfb = (time.monotonic() - ai_response_start_time) * 1000
                                    logger.info(f"TTFB (Time to First Byte): {ttfb:.2f}ms")
                                    ttfb_logged = True
                                    
                                event = AgentChunkEvent.create(sentence)
                                
                                # Speculative handling: if speculative, wait for promotion
                                if speculative:
                                    if not promotion_event.is_set():
                                        logger.debug(f"Holding speculative chunk: {sentence}")
                                        try:
                                            # Wait for promotion or cancellation
                                            await promotion_event.wait()
                                        except asyncio.CancelledError:
                                            raise
                                            
                                logger.info(f"Agent says (chunk): {sentence}")
                                await output_queue.put(event)
                            current_sentence = ""

            final = current_sentence.strip()
            if final:
                if "[END_CALL]" in final:
                    final = final.replace("[END_CALL]", "").strip()
                    if final:
                        logger.info(f"Agent says (final): {final}")
                        await output_queue.put(AgentChunkEvent.create(final))
                    logger.info("Hangup marker [END_CALL] detected. Signaling hangup.")
                    await output_queue.put(HangupEvent.create(reason="natural_end"))
                else:
                    logger.info(f"Agent says (final): {final}")
                    await output_queue.put(AgentChunkEvent.create(final))
        except asyncio.CancelledError:
            logger.info("AI response cancelled (barge-in)")
        except Exception as e:
            # Check for specific quota/api errors
            error_str = str(e).lower()
            if any(term in error_str for term in ["quota", "rate limit", "429", "insufficient_quota"]):
                logger.error(f"Quota/Rate Limit Error: {e}")
                
                # Localize the error message based on platform config
                try:
                    from services.config_service import get_platform_config
                    config = await get_platform_config()
                    lang = config.get("default_language", "hi")
                except Exception:
                    lang = "hi"
                
                error_msgs = {
                    "hi": "माफ कीजियेगा, मेरे सर्वर में थोड़ी तकनीकी परेशानी आ रही है। आप थोड़ी देर बाद फिर से कॉल कीजिये। नमस्ते!",
                    "en": "I'm sorry, I'm experiencing some technical difficulties with my server. Please call back in a little while. Namaste!",
                    "pa": "ਮਾਫ ਕਰਨਾ, ਮੇਰੇ ਸਰਵਰ ਵਿੱਚ ਕੁਝ ਤਕਨੀਕੀ ਮੁਸ਼ਕਲਾਂ ਆ ਰਹੀਆਂ ਹਨ। ਕਿਰਪਾ ਕਰਕੇ ਕੁਝ ਸਮੇਂ ਬਾਅਦ ਦੁਬਾਰਾ ਕਾਲ ਕਰੋ। ਨਮਸਤੇ!",
                    "mr": "क्षमस्व, माझ्या सर्व्हरमध्ये काही तांत्रिक अडचणी येत आहेत. कृपया थोड्या वेळाने पुन्हा कॉल करा. नमस्ते!"
                }
                await output_queue.put(AgentChunkEvent.create(error_msgs.get(lang, error_msgs["hi"])))
                await output_queue.put(HangupEvent.create(reason="quota_exceeded"))
                return
            if "tool_calls" in error_str and ("ToolMessage" in error_str or "not have response messages" in error_str or "400" in error_str or "invalid_request_error" in error_str):
                logger.warning("Detected tool call state corruption. Attempting to fix state by removing dangling tool calls.")
                try:
                    state = await session_agent_executor.aget_state({"configurable": {"thread_id": thread_id}})
                    messages = state.values.get("messages", [])
                    
                    patched = False
                    for msg in reversed(messages):
                        if getattr(msg, "tool_calls", None):
                            from langchain_core.messages import AIMessage
                            # Overwrite the message to remove the dangling tool calls
                            new_msg = AIMessage(
                                content=msg.content or "[Action interrupted by user]", 
                                id=msg.id,
                                tool_calls=[]
                            )
                            await session_agent_executor.aupdate_state(
                                {"configurable": {"thread_id": thread_id}},
                                {"messages": [new_msg]}
                            )
                            logger.info(f"Successfully patched state by removing tool calls from message {msg.id}. Retrying...")
                            patched = True
                            await generate_ai_response(text)
                            return
                            
                    if not patched:
                        logger.warning("Could not find message with tool_calls to patch. Falling back to rotating thread_id.")
                        thread_id = str(uuid4())
                        await generate_ai_response(text)
                        return
                    
                except Exception as patch_e:
                    logger.error(f"Failed to patch state: {patch_e}", exc_info=True)
                    logger.warning("Falling back to rotating thread_id.")
                    thread_id = str(uuid4())
                    await generate_ai_response(text)
            else:
                logger.error(f"AI response error: {e}", exc_info=True)

    def _in_grace_period() -> bool:
        """Check if we're still in the barge-in grace period."""
        return (time.monotonic() - ai_response_start_time) < BARGE_IN_GRACE_PERIOD

    def _start_ai_task(text: str):
        """Start a new AI response task, cancelling any in-flight one."""
        nonlocal current_ai_task, ai_response_start_time
        if current_ai_task and not current_ai_task.done():
            current_ai_task.cancel()
        ai_response_start_time = time.monotonic()
        current_ai_task = asyncio.create_task(generate_ai_response(text))

    last_stt_text: str = ""

    async def upstream_listener():
        """Consume STT events and drive the agent conversation."""
        nonlocal current_ai_task, last_stt_text, speculative_text, speculative_task, promotion_event
        consecutive_timeouts = 0
        try:
            event_iter = event_stream.__aiter__()
            while True:
                # If AI is currently answering, we do NOT timeout
                is_ai_speaking = current_ai_task and not current_ai_task.done()
                timeout_duration = None if is_ai_speaking else 10.0

                try:
                    if timeout_duration:
                        event = await asyncio.wait_for(anext(event_iter), timeout=timeout_duration)
                    else:
                        event = await anext(event_iter)
                        
                    # We received an event from STT (background noise, stt_chunk, etc)
                    # We only reset the timeout if it's actual speech output or start
                    if getattr(event, "type", "") in ["stt_output", "stt_chunk", "call_started"]:
                        consecutive_timeouts = 0

                except asyncio.TimeoutError:
                    if is_ai_speaking:
                        continue
                        
                    consecutive_timeouts += 1
                    logger.info(f"User silence timeout #{consecutive_timeouts} detected.")
                    
                    if consecutive_timeouts == 1:
                        _start_ai_task("__USER_SILENCE__")
                    elif consecutive_timeouts >= 2:
                        _start_ai_task("__USER_SILENCE_FINAL__")
                    continue
                except StopAsyncIteration:
                    break

                if event.type == "call_started":
                    # Trigger greeting immediately when pipeline starts
                    logger.info("Triggering initial greeting")
                    last_stt_text = ""
                    _start_ai_task("__CALL_STARTED__")
                    continue

                if event.type == "barge_in":
                    if _in_grace_period():
                        logger.info(f"Barge-in ignored (grace period: {time.monotonic() - ai_response_start_time:.2f}s)")
                        continue
                    if current_ai_task and not current_ai_task.done():
                        logger.info("Barge-in: cancelling AI task")
                        current_ai_task.cancel()
                    # Pass through for downstream (TTS needs it)
                    await output_queue.put(event)
                    continue

                # Pass through non-barge-in events (stt_chunk, stt_output)
                await output_queue.put(event)

                if event.type == "stt_interim":
                    text = event.transcript.strip()
                    if not text or len(text) < 10:
                        continue
                        
                    # If this matches our current speculative work, do nothing
                    if text == speculative_text:
                        continue
                        
                    # If AI is already responding to a FINAL transcript, ignore interims
                    if current_ai_task and not current_ai_task.done():
                        continue
                        
                    # New or different interim -> Start speculative task
                    logger.info("Starting speculative AI task for: %s", text)
                    if speculative_task and not speculative_task.done():
                        speculative_task.cancel()
                    
                    promotion_event.clear()
                    speculative_text = text
                    ai_response_start_time = time.monotonic()
                    speculative_task = asyncio.create_task(generate_ai_response(text, speculative=True))
                    continue

                if event.type == "stt_output":
                    text = event.transcript.strip()
                    if not text:
                        continue
                        
                    # Noise filtering
                    whitelist = ["जी", "हां", "ना", "ji", "yes", "no", "ok", "ओके"]
                    if len(text) < 3 and text.lower() not in whitelist:
                        logger.info("Ignoring short noise artifact: '%s'", text)
                        continue
                        
                    if text == last_stt_text:
                        logger.info("Ignoring duplicate STT text: %s", text)
                        continue
                    last_stt_text = text

                    # CATCH & PROMOTE: If the finalized text matches our speculative work, promote it
                    # We allow minor differences (case, punctuation) or if the final matches exactly what we speculated on.
                    # Or even if the final is just the speculated text + more words, it's often close enough to keep.
                    if speculative_task and not speculative_task.done() and (text.startswith(speculative_text) or speculative_text.startswith(text)):
                        logger.info("Speculative match! Promoting AI task for: %s", text)
                        promotion_event.set()
                        current_ai_task = speculative_task
                        speculative_task = None
                        speculative_text = ""
                    else:
                        # No match or no speculation: Start fresh FINAL response
                        logger.info("Starting fresh FINAL AI task for: %s", text)
                        if speculative_task and not speculative_task.done():
                            speculative_task.cancel()
                        
                        if current_ai_task and not current_ai_task.done():
                            current_ai_task.cancel()
                            
                        ai_response_start_time = time.monotonic()
                        current_ai_task = asyncio.create_task(generate_ai_response(text, speculative=False))
                    continue
        finally:
            await output_queue.put(None)

    asyncio.create_task(upstream_listener())

    while True:
        event = await output_queue.get()
        if event is None:
            break
        yield event
