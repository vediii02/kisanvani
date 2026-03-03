import asyncio
import time
from typing import AsyncIterator
from uuid import uuid4

from langchain_core.messages import HumanMessage
from services.voice.events import VoiceAgentEvent, AgentChunkEvent, BargeInEvent
from services.voice.llm import get_agent_executor
from services.voice.logger import setup_logger
from services.voice.session_context import get_current_organisation_id, get_current_company_id

logger = setup_logger("agent_node")

# How many seconds to ignore barge-in after starting an AI response
BARGE_IN_GRACE_PERIOD = 4.0


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
    thread_id = str(uuid4())
    output_queue: asyncio.Queue = asyncio.Queue()
    current_ai_task: asyncio.Task | None = None
    ai_response_start_time: float = 0.0  # When the current AI response started
    session_org_id = get_current_organisation_id()
    session_comp_id = get_current_company_id()
    session_agent_executor = await get_agent_executor(session_org_id, session_comp_id)
    logger.info("Agent session started: org_id=%s, company_id=%s, thread=%s", session_org_id, session_comp_id, thread_id[:8])

    async def generate_ai_response(text: str):
        """Stream LLM response into the shared output queue, chunked by sentence."""
        try:
            stream = session_agent_executor.astream(
                {"messages": [HumanMessage(content=text)]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            )
            current_sentence = ""
            async for message, metadata in stream:
                # AIMessageChunk has .type == 'AIMessageChunk', not 'ai'
                is_ai = hasattr(message, 'content') and 'ai' in message.type.lower()
                # Skip tool calls/responses
                is_tool = getattr(message, 'tool_calls', None) or getattr(message, 'tool_call_chunks', None)
                
                if is_ai and message.content and not is_tool:
                    chunk = message.content
                    if isinstance(chunk, list):
                        chunk = "".join([
                            c.get("text", "") for c in chunk
                            if isinstance(c, dict) and "text" in c
                        ])

                    for char in chunk:
                        current_sentence += char
                        if char in ['.', '!', '?', '।', '\n']:
                            sentence = current_sentence.strip()
                            if sentence:
                                logger.info(f"Agent says: {sentence}")
                                await output_queue.put(
                                    AgentChunkEvent.create(sentence)
                                )
                            current_sentence = ""

            final = current_sentence.strip()
            if final:
                logger.info(f"Agent says (final): {final}")
                await output_queue.put(AgentChunkEvent.create(final))
        except asyncio.CancelledError:
            logger.info("AI response cancelled (barge-in)")
        except Exception as e:
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

    async def upstream_listener():
        """Consume STT events and drive the agent conversation."""
        nonlocal current_ai_task
        try:
            async for event in event_stream:
                if event.type == "call_started":
                    # Trigger greeting immediately when pipeline starts
                    logger.info("Triggering initial greeting")
                    _start_ai_task("__CALL_STARTED__")
                    continue

                if event.type == "barge_in":
                    if _in_grace_period():
                        logger.info("Barge-in ignored (grace period)")
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
                    # New user utterance → start new AI response
                    _start_ai_task(event.transcript)
        finally:
            await output_queue.put(None)

    asyncio.create_task(upstream_listener())

    while True:
        event = await output_queue.get()
        if event is None:
            break
        yield event
