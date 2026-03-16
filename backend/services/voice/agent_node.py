import asyncio
import re
import time
from collections import OrderedDict
from typing import AsyncIterator
from uuid import uuid4

from langchain_core.messages import HumanMessage
from services.voice.events import VoiceAgentEvent, AgentChunkEvent, BargeInEvent, HangupEvent, FillerAudioEvent, AgentEndEvent
from services.voice.llm import get_agent_executor
from services.voice.logger import setup_logger
from services.voice.session_context import (
    get_current_organisation_id, 
    get_current_company_id, 
    get_current_session_id,
    session_state_manager
)

logger = setup_logger("agent_node")

# Concurrency locks for shared module state
_cache_lock = asyncio.Lock()

# How many seconds to ignore barge-in after starting an AI response
BARGE_IN_GRACE_PERIOD = 0.2

# Module-level caches for cross-turn optimizations
MAX_CONTEXT_CACHE_SIZE = 200
_context_cache: OrderedDict = OrderedDict() 
_interrupted_threads = set() # Set of thread_ids that were interrupted and need state healing

def clear_agent_context(thread_id: str):
    """Refine 5: Cleanup cache on call end."""
    if thread_id in _context_cache:
        _context_cache.pop(thread_id, None)
    if thread_id in _interrupted_threads:
        _interrupted_threads.remove(thread_id)
    logger.info(f"Cleared agent context for {thread_id}")


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
    raw_session_id = get_current_session_id()
    thread_id = raw_session_id or str(uuid4())
    logger.info("Agent session started. session_id (raw): %s, thread_id (used): %s", raw_session_id, thread_id)
    
    # Refine 4: Bound queue size to prevent memory growth
    output_queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    current_ai_task: asyncio.Task | None = None
    ai_response_start_time: float = 0.0  # When the current AI response started
    
    async def _run_stream(executor, text, thread_id, output_queue):
        """Internal helper to execute the LLM stream and push to output_queue."""
        sid = get_current_session_id()
        state = session_state_manager.get_state(sid) if sid else None
        current_turn = state.new_turn() if state else 0
        
        try:
            from langchain_core.messages import HumanMessage
            stream = executor.astream(
                {"messages": [HumanMessage(content=text)]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            )
            current_sentence = ""
            sent_first_chunk = False
            async for chunk, metadata in stream:
                # Check for global interrupt
                sid = get_current_session_id()
                state = session_state_manager.get_state(sid) if sid else None
                if state and state.is_interrupted:
                    logger.info("Agent: Global interrupt detected. Aborting LLM stream and flushing queue.")
                    # Drain the local queue to stop chunks from propagating
                    while not output_queue.empty():
                        try:
                            output_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                    break

                if isinstance(chunk, str) or isinstance(chunk, dict):
                    continue
                message = chunk
                valid_nodes = ["greeting", "profiling", "diagnostic", "advisory"]
                if not metadata or metadata.get("langgraph_node") not in valid_nodes:
                    continue

                is_ai = hasattr(message, 'content') and 'ai' in message.type.lower()
                if getattr(message, "chunk", None) == False:
                    continue

                is_tool = bool(getattr(message, 'tool_calls', None))
                if is_tool:
                    for tool_call in message.tool_calls:
                        if tool_call.get("name") == "end_call":
                            await output_queue.put(HangupEvent.create(reason="agent_ended_call"))
                
                if is_ai and message.content and not is_tool:
                    content = message.content
                    if isinstance(content, list):
                        content = "".join([c.get("text", "") for c in content if isinstance(c, dict) and "text" in c])
                    content = re.sub(r'<function=\w+>.*?</function>', '', content, flags=re.DOTALL)
                    content = re.sub(r'<function=\w+>.*', '', content, flags=re.DOTALL)
                    if not content.strip():
                        continue
                        
                    CHUNK_CHARS = {'.', '!', '?', '।', '\n', '،', ':', ';'}
                    
                    for char in content:
                        current_sentence += char
                        words = current_sentence.split()
                        
                        # Dynamic chunking: First chunk is small for low TTFB, subsequent chunks are larger for prosody
                        min_words = 4 if not sent_first_chunk else 10
                        
                        should_chunk = (
                            char in CHUNK_CHARS and len(words) >= 3 # require a small phrase for punct
                        ) or (char.isspace() and len(words) >= min_words)
                        
                        if should_chunk:
                            sentence = current_sentence.strip()
                            if sentence:
                                sent_first_chunk = True
                                logger.info(f"Agent says: {sentence}")
                                try:
                                    output_queue.put_nowait(AgentChunkEvent.create(sentence, turn_id=current_turn))
                                except asyncio.QueueFull:
                                    logger.warning("Output queue full, dropping agent chunk")
                            current_sentence = ""
            final = current_sentence.strip()
            if final:
                logger.info(f"Agent says (final): {final}")
                try:
                    output_queue.put_nowait(AgentChunkEvent.create(final, turn_id=current_turn))
                except asyncio.QueueFull:
                    logger.warning("Output queue full, dropping agent chunk")
            
            # Signal TTS to flush after full response
            try:
                output_queue.put_nowait(AgentEndEvent.create())
            except asyncio.QueueFull:
                pass
            
            # Clean completion: remove from interrupted set
            # Refine 1: Concurrency protection
            async with _cache_lock:
                if thread_id in _interrupted_threads:
                    _interrupted_threads.remove(thread_id)
                
        except asyncio.CancelledError:
            # Mark for state healing on next turn
            # Refine 1: Concurrency protection
            async with _cache_lock:
                _interrupted_threads.add(thread_id)
            logger.info(f"AI response cancelled (barge-in). Thread {thread_id} marked for healing.")
            raise

    async def generate_ai_response(text: str):
        """Stream LLM response into the shared output queue, chunked by sentence."""
        nonlocal thread_id
        # Refine 2: Fix UnboundLocalError
        executor = None
        try:
            # Fix 4: Cache DB context recovery
            # Refine 1: Concurrency protection
            async with _cache_lock:
                cached = _context_cache.get(thread_id)
            
            if cached:
                org_id = cached.get("org_id")
                comp_id = cached.get("comp_id")
                from services.voice.session_context import (
                    set_current_organisation_id, set_current_phone_number, set_current_farmer_row_id
                )
                set_current_organisation_id(org_id)
                set_current_phone_number(cached.get("phone"))
                if cached.get("farmer_id"):
                    set_current_farmer_row_id(cached.get("farmer_id"))
            else:
                org_id = get_current_organisation_id()
                comp_id = get_current_company_id()
                if thread_id:
                    try:
                        from db.base import AsyncSessionLocal
                        from db.models.call_session import CallSession
                        from sqlalchemy import select
                        from services.voice.session_context import (
                            set_current_organisation_id, set_current_company_id,
                            set_current_phone_number, set_current_farmer_row_id
                        )
                        logger.info(f"Generating AI response for {thread_id}: attempting context recovery")
                        async with asyncio.timeout(5.0): # Fix: Add specific timeout for recovery
                            async with AsyncSessionLocal() as db:
                                res = (await db.execute(
                                    select(CallSession.organisation_id, CallSession.from_phone, CallSession.phone_number, CallSession.farmer_id)
                                    .where(CallSession.session_id == thread_id)
                                )).first()
                                if res:
                                    db_org_id, db_from, db_phone, db_farmer = res
                                    if org_id is None: org_id = db_org_id
                                    phone = db_from or db_phone
                                    set_current_organisation_id(org_id)
                                    if phone: set_current_phone_number(phone)
                                    if db_farmer: set_current_farmer_row_id(int(db_farmer))
                                    
                                    # Fix 4: Max-size eviction to prevent memory leak
                                    # Refine 1: Concurrency protection
                                    async with _cache_lock:
                                        _context_cache[thread_id] = {
                                            "org_id": org_id,
                                            "comp_id": comp_id,
                                            "phone": phone,
                                            "farmer_id": int(db_farmer) if db_farmer else None
                                        }
                                        if len(_context_cache) > MAX_CONTEXT_CACHE_SIZE:
                                            _context_cache.popitem(last=False)
                                        
                                    logger.info(f"Context recovered and cached for {thread_id}")
                    except asyncio.TimeoutError:
                        logger.error(f"Context recovery TIMEOUT for {thread_id} - proceeding with defaults")
                    except Exception as e:
                        logger.warning("Agent task failed to recover context: %s", e)

            executor = await get_agent_executor(org_id, comp_id)

            # Fix 5: Conditional state healer
            # Refine 1: Concurrency protection
            should_heal = False
            async with _cache_lock:
                should_heal = thread_id in _interrupted_threads

            if should_heal:
                logger.info(f"Thread {thread_id} marked for healing - attempting state patch")
                try:
                    async with asyncio.timeout(3.0): # Fix: Add timeout for healer
                        state = await executor.aget_state({"configurable": {"thread_id": thread_id}})
                        messages = state.values.get("messages", [])
                        if messages and getattr(messages[-1], "tool_calls", None):
                            last_msg = messages[-1]
                            logger.warning(f"Conditional healer patching dangling tool calls in {last_msg.id}")
                            from langchain_core.messages import AIMessage
                            new_msg = AIMessage(content=last_msg.content or "[Interrupted]", id=last_msg.id, tool_calls=[])
                            await executor.aupdate_state({"configurable": {"thread_id": thread_id}}, {"messages": [new_msg]})
                except asyncio.TimeoutError:
                    logger.error(f"Healer TIMEOUT for {thread_id}")
                except Exception as e:
                    logger.debug(f"Healer skip: {e}")

            # Fix 8: Refactored streaming logic
            await _run_stream(executor, text, thread_id, output_queue)
        except asyncio.CancelledError:
            logger.info("AI response cancelled (barge-in)")
        except Exception as e:
            if executor is None:
                logger.error(f"Failed to initialize executor: {e}")
                return

            error_str = str(e)
            if "tool_calls" in error_str and ("ToolMessage" in error_str or "not have response messages" in error_str or "400" in error_str or "invalid_request_error" in error_str):
                logger.warning("Detected tool call state corruption. Patching ALL dangling tool calls in one pass.")
                try:
                    state = await executor.aget_state({"configurable": {"thread_id": thread_id}})
                    messages = state.values.get("messages", [])
                    
                    # Patch ALL messages with dangling tool calls in a single pass
                    patches = []
                    for msg in messages:
                        if getattr(msg, "tool_calls", None):
                            from langchain_core.messages import AIMessage
                            patches.append(AIMessage(
                                content=msg.content or "[Action interrupted by user]", 
                                id=msg.id,
                                tool_calls=[]
                            ))
                    
                    if patches:
                        for patch in patches:
                            try:
                                async with asyncio.timeout(2.0):
                                    await executor.aupdate_state(
                                        {"configurable": {"thread_id": thread_id}},
                                        {"messages": [patch]}
                                    )
                            except (asyncio.CancelledError, asyncio.TimeoutError):
                                logger.error(f"Patch update TIMEOUT for {thread_id}")
                                break
                        logger.info(f"Patched {len(patches)} dangling tool call message(s). Retrying once.")
                        # Single retry using shared helper
                        await _run_stream(executor, text, thread_id, output_queue)
                    else:
                        logger.warning("No dangling tool calls found to patch. Turn may fail but session is preserved.")
                except Exception as patch_e:
                    logger.error(f"Failed to patch state: {patch_e}", exc_info=True)
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
        nonlocal current_ai_task, last_stt_text
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
                    
                    logger.debug(f"Agent Listener: Received event type={getattr(event, 'type', 'unknown')}")
                        
                    # Proactive VAD/GlobalState interrupt check
                    sid = get_current_session_id()
                    state = session_state_manager.get_state(sid) if sid else None
                    if state and state.is_interrupted:
                        if current_ai_task and not current_ai_task.done():
                            logger.info("Agent Listener: Proactive interrupt from GlobalState. Cancelling AI task.")
                            current_ai_task.cancel()
                            try:
                                async with asyncio.timeout(2.0): # Fix: Add timeout for cancellation cleanup
                                    await current_ai_task # Wait for cancellation cleanup
                            except (asyncio.CancelledError, asyncio.TimeoutError):
                                pass
                            # Drain output_queue to clear any residual chunks
                            while not output_queue.empty():
                                try:
                                    output_queue.get_nowait()
                                except asyncio.QueueEmpty:
                                    break

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
                    if event.session_id:
                        logger.info("Recovered thread_id from CallStartedEvent: %s", event.session_id)
                        thread_id = event.session_id
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
                        try:
                            async with asyncio.timeout(2.0): # Fix: Add timeout for barge-in cancellation
                                await current_ai_task # Await for hard cleanup
                        except (asyncio.CancelledError, asyncio.TimeoutError):
                            pass
                    
                    # Refine: Drain output_queue to prevent stale chunks from reaching TTS
                    while not output_queue.empty():
                        try:
                            output_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                            
                    # Pass through for downstream (TTS needs it)
                    await output_queue.put(event)
                    continue

                # Pass through non-barge-in events (stt_chunk, stt_output)
                await output_queue.put(event)

                if event.type == "stt_output":
                    text = event.transcript.strip()
                    if not text:
                        continue
                    # Avoid processing the exact same text twice in rapid succession
                    if text == last_stt_text:
                        logger.info("Ignoring duplicate STT text: %s", text)
                        continue
                    last_stt_text = text
                    
                    # Fix 6: Start AI task BEFORE sending filler to reduce overlap risk
                    _start_ai_task(text)

                    # TTFB Masking - Gate filler words on word count/triggers
                    urgent_trigger_words = [
                        "upay", "dawai", "ilaj", "product", "medicine", "solution", 
                        "kya dalu", "kya karu", "bimari", "keeda", "pests", "rog",
                        "उपाय", "दवाई", "इलाज", "बीमारी", "कीड़ा", "रोग"
                    ]
                    if any(w in text.lower() for w in urgent_trigger_words) or len(text.split()) >= 2:
                        await output_queue.put(FillerAudioEvent.create())
        finally:
            await output_queue.put(None)

    asyncio.create_task(upstream_listener())

    while True:
        event = await output_queue.get()
        if event is None:
            break
        yield event
