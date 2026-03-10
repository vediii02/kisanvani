
import asyncio
import os
import sys
from uuid import uuid4

# Add app to path
sys.path.append(os.getcwd())

from services.voice.llm import get_agent_executor, init_checkpointer
from services.voice.session_context import (
    set_current_organisation_id,
    set_current_company_id,
    set_current_phone_number,
)
from langchain_core.messages import HumanMessage

async def run_test(query: str):
    print(f"Running test for query: {query}")
    print("Initializing checkpointer...", flush=True)
    await init_checkpointer()
    print("Checkpointer initialized.", flush=True)
    
    org_id = 2
    comp_id = 1
    set_current_organisation_id(org_id)
    set_current_company_id(comp_id)
    set_current_phone_number("+910000000001")
    thread_id = str(uuid4())
    
    executor = await get_agent_executor(org_id, comp_id)
    
    print(f"Agent ready! Thread ID: {thread_id}")
    
    # Simulate conversation
    messages = [HumanMessage(content="__CALL_STARTED__"), HumanMessage(content=query)]
    
    for msg in messages:
        print(f"\n--- Sending to Agent: {msg.content} ---", flush=True)
        try:
            stream = executor.astream(
                {"messages": [msg]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages"
            )
            print("[DEBUG] Stream created, iterating chunks...", flush=True)
            
            async for chunk, metadata in stream:
                if isinstance(chunk, str) or isinstance(chunk, dict):
                    continue
                
                message = chunk
                valid_nodes = ["greeting", "profiling", "diagnostic", "advisory", "tools"]
                if not metadata or metadata.get("langgraph_node") not in valid_nodes:
                    continue
                
                print(f"[DEBUG] Node: {metadata.get('langgraph_node')}", flush=True)
                
                is_ai = hasattr(message, 'content') and 'ai' in message.type.lower()
                if is_ai and message.content:
                    is_tool = getattr(message, "tool_calls", None) or getattr(message, "tool_call_chunks", None)
                    if getattr(message, "chunk", None) == False: 
                        continue
                    if not is_tool:
                        print(f"Agent Response: {message.content}", flush=True)
                
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tc in message.tool_calls:
                        print(f"\n[Tool Call Triggered: {tc['name']}({tc['args']})]", flush=True)
            print("[DEBUG] Stream finished for this message.", flush=True)
        except Exception as e:
            print(f"[ERROR] during stream processing: {e}", flush=True)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    query = "Dhan mein soondi ka ilaaj bataye"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    asyncio.run(run_test(query))
