import asyncio
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

async def test_init():
    print("Testing LLM initialization...")
    from services.voice.llm import get_agent_executor, init_checkpointer
    
    print("Initializing checkpointer...")
    await init_checkpointer()
    
    print("Getting agent executor for org=None, company=None...")
    try:
        executor = await get_agent_executor(None, None)
        print("Success! Agent executor created.")
        
        # Test a simple invocation
        print("Testing a stream invocation...")
        async for chunk in executor.astream(
            {"messages": [("user", "hi")]},
            {"configurable": {"thread_id": "test_thread"}},
            stream_mode="messages"
        ):
            message, metadata = chunk
            print(f"Received chunk from node: {metadata.get('langgraph_node')}")
            if hasattr(message, 'content'):
                print(f"Content: {message.content[:50]}...")
        print("Test complete.")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_init())
