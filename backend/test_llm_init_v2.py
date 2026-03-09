import asyncio
import os
import sys
import time

# Add current dir to path
sys.path.append(os.getcwd())

async def test_init():
    print(">>> 1. Manual diagnostic start")
    from services.voice.llm import get_agent_executor, init_checkpointer, get_llm
    
    print(">>> 2. Initializing checkpointer...")
    start = time.monotonic()
    try:
        await asyncio.wait_for(init_checkpointer(), timeout=10)
        print(f">>> 3. Checkpointer OK ({time.monotonic()-start:.2f}s)")
    except Exception as e:
        print(f">>> 3. Checkpointer FAILED: {e}")
        return

    print(">>> 4. Testing get_llm()...")
    try:
        llm = await asyncio.wait_for(get_llm(), timeout=10)
        print(f">>> 5. LLM OK ({llm})")
    except Exception as e:
        print(f">>> 5. LLM FAILED: {e}")
        return

    print(">>> 6. Getting agent executor for org=None, company=None...")
    try:
        executor = await get_agent_executor(None, None)
        print(">>> 7. Success! Agent executor created.")
        
        # Test a simple invocation
        print(">>> 8. Testing a stream invocation (Timeout 15s)...")
        stream = executor.astream(
            {"messages": [("user", "hi")]},
            {"configurable": {"thread_id": "test_thread_" + str(time.time())}},
            stream_mode="messages"
        )
        
        async for chunk in stream:
            message, metadata = chunk
            node = metadata.get('langgraph_node')
            content = message.content[:30] if hasattr(message, 'content') else "No content"
            print(f">>> 9. Chunk from [{node}]: {content}...")
            if node == 'greeting' or node == 'advisory':
                print(">>> 10. Received valid response node.")
                break
        print(">>> 11. Test complete.")
    except Exception as e:
        print(f">>> FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_init())
