import asyncio
import os
import sys
import time
from uuid import uuid4

# Add app to path
sys.path.append(os.getcwd())

from services.voice.llm import get_agent_executor, init_checkpointer
from langchain_core.messages import HumanMessage

async def verify_latency():
    print("Initializing agent...")
    await init_checkpointer()
    
    org_id = 1
    comp_id = 1
    thread_id = str(uuid4())
    executor = await get_agent_executor(org_id, comp_id)
    
    print(f"\n--- Testing Latency for Advisory Stage ---")
    query = "Dhan mein soondi ka ilaaj bataye"
    print(f"Query: {query}")
    
    start_time = time.monotonic()
    chunks = []
    
    stream = executor.astream(
        {"messages": [HumanMessage(content=query)]},
        {"configurable": {"thread_id": thread_id}},
        stream_mode="messages"
    )
    
    first_chunk_time = None
    
    async for chunk, metadata in stream:
        if isinstance(chunk, str) or isinstance(chunk, dict):
            continue
            
        message = chunk
        valid_nodes = ["advisory", "advisory_preamble"]
        if not metadata or metadata.get("langgraph_node") not in valid_nodes:
            continue
            
        node_name = metadata.get("langgraph_node")
        is_ai = hasattr(message, 'content') and 'ai' in message.type.lower()
        if is_ai and message.content:
            if getattr(message, "chunk", None) == False:
                continue
            
            if not first_chunk_time:
                first_chunk_time = time.monotonic()
                ttfb = (first_chunk_time - start_time) * 1000
                print(f"\n[METRIC] TTFB (First Node Reach): {ttfb:.2f}ms")
            
            content = message.content
            print(f"[{node_name}] AI: {content}")
            chunks.append(content)

    end_time = time.monotonic()
    total_duration = (end_time - start_time) * 1000
    print(f"\n[METRIC] Total Response Duration: {total_duration:.2f}ms")
    
    if len(chunks) >= 2:
        print("\nSUCCESS: Received both speculative empathy and grounded advice.")
    else:
        print("\nWARNING: Unexpected number of chunks received.")

if __name__ == "__main__":
    asyncio.run(verify_latency())
