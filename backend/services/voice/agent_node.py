import asyncio
import re
import time
from typing import AsyncIterator
from uuid import uuid4

from langchain_core.messages import HumanMessage
from services.voice.events import VoiceAgentEvent, AgentChunkEvent, BargeInEvent, HangupEvent
from services.voice.llm import get_agent_executor
from services.voice.logger import setup_logger
from services.voice.session_context import get_current_organisation_id, get_current_company_id, get_current_session_id

logger = setup_logger("agent_node")

# How many seconds to ignore barge-in after starting an AI response
BARGE_IN_GRACE_PERIOD = 1.0


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
    
    output_queue: asyncio.Queue = asyncio.Queue()
    current_ai_task: asyncio.Task | None = None
    ai_response_start_time: float = 0.0  # When the current AI response started
    async def generate_ai_response(text: str):
        """Stream LLM response into the shared output queue, chunked by sentence."""
        nonlocal thread_id
        try:
            # Dynamically resolve context for this AI response
            # This ensures we pick up late-binding Org/Company IDs (e.g. from Exotel start event)
            org_id = get_current_organisation_id()
            comp_id = get_current_company_id()
            
            # If org_id is missing, try to recover it from session DB (safety fallback)
            if org_id is None and thread_id:
                try:
                    from db.base import AsyncSessionLocal
                    from db.models.call_session import CallSession
                    from sqlalchemy import select
                    from services.voice.session_context import set_current_organisation_id, set_current_company_id
                    async with AsyncSessionLocal() as db:
                        res = (await db.execute(
                            select(CallSession.organisation_id, CallSession.company_id)
                            .where(CallSession.session_id == thread_id)
                        )).first()
                        if res and res[0]:
                            org_id = res[0]
                            set_current_organisation_id(org_id)
                            if res[1]:
                                comp_id = res[1]
                                set_current_company_id(comp_id)
                            logger.info("Task recovered context from DB: org_id=%s", org_id)
                except Exception as e:
                    logger.warning("Agent task failed to recover context: %s", e)

            executor = await get_agent_executor(org_id, comp_id)
            

            # Proactive state healing before invoking the LLM
            # If the previous turn was interrupted during a tool call,
            # LangGraph state will contain an AIMessage with tool_calls but no matching ToolMessage.
            try:
                state = await executor.aget_state({"configurable": {"thread_id": thread_id}})
                messages = state.values.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if getattr(last_msg, "tool_calls", None):
                        logger.warning(f"Proactive state healer found dangling tool calls in message {last_msg.id}. Patching...")
                        from langchain_core.messages import AIMessage
                        # Overwrite the message to remove the dangling tool calls
                        new_msg = AIMessage(
                            content=last_msg.content or "[Action interrupted by user]",
                            id=last_msg.id,
                            tool_calls=[]
                        )
                        await executor.aupdate_state(
                            {"configurable": {"thread_id": thread_id}},
                            {"messages": [new_msg]}
                        )
                        logger.info("Successfully patched dangling tool calls before LLM invocation.")
            except Exception as e:
                logger.debug(f"State healer skipped (normal for new sessions): {e}")

            stream = executor.astream(
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

                # Detect specific tool calls for workflow control
                is_tool = False
                if getattr(message, 'tool_calls', None):
                    is_tool = True
                    for tool_call in message.tool_calls:
                        if tool_call.get("name") == "end_call":
                            logger.info("Agent decided to end the call via tool.")
                            await output_queue.put(HangupEvent.create(reason="agent_ended_call"))
                
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

                    # Fast streaming chunker: pushes immediately when a sentence ends
                    # Reduces "time to first audio" latency significantly
                    for char in chunk:
                        current_sentence += char
                        # Trigger on common Hindi/English sentence terminators
                        if char in {'.', '!', '?', '।', '\n'}:
                            sentence = current_sentence.strip()
                            if sentence:
                                logger.info(f"Agent says: {sentence}")
                                await output_queue.put(AgentChunkEvent.create(sentence))
                            current_sentence = ""

            final = current_sentence.strip()
            if final:
                logger.info(f"Agent says (final): {final}")
                await output_queue.put(AgentChunkEvent.create(final))
        except asyncio.CancelledError:
            logger.info("AI response cancelled (barge-in)")
        except Exception as e:
            error_str = str(e)
            if "tool_calls" in error_str and ("ToolMessage" in error_str or "not have response messages" in error_str or "400" in error_str or "invalid_request_error" in error_str):
                logger.warning("Detected tool call state corruption despite proactive healer. Attempting to fix state by removing dangling tool calls.")
                try:
                    state = await executor.aget_state({"configurable": {"thread_id": thread_id}})
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
                            await executor.aupdate_state(
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
                    # New user utterance → start new AI response
                    _start_ai_task(text)
        finally:
            await output_queue.put(None)

    asyncio.create_task(upstream_listener())

    while True:
        event = await output_queue.get()
        if event is None:
            break
        yield event
