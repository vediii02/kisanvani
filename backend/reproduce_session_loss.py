
import asyncio
from services.voice.session_context import set_current_session_id, get_current_session_id
from services.voice.agent_node import agent_stream
from services.voice.events import STTOutputEvent
from langchain_core.runnables import RunnableGenerator

async def mock_stt_stream():
    yield STTOutputEvent.create(transcript="Hello")
    await asyncio.sleep(0.5)
    yield STTOutputEvent.create(transcript="My name is Ramesh")
    await asyncio.sleep(0.5)

async def test_context():
    session_id = "test_stable_session_123"
    token = set_current_session_id(session_id)
    print(f"Set session_id in main task: {get_current_session_id()}")
    
    pipeline = RunnableGenerator(agent_stream)
    
    try:
        async for event in pipeline.astream(mock_stt_stream()):
            print(f"Event received: {event.type}")
    finally:
        from services.voice.session_context import reset_current_session_id
        reset_current_session_id(token)

if __name__ == "__main__":
    asyncio.run(test_context())
