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

async def main():
    print("Initializing agent...")
    await init_checkpointer()
    
    # Use default org/comp IDs
    org_id = 1
    comp_id = 1
    set_current_organisation_id(org_id)
    set_current_company_id(comp_id)
    # Test harness: ensure profile tool has a session phone key.
    set_current_phone_number("+910000000001")
    thread_id = str(uuid4())
    
    executor = await get_agent_executor(org_id, comp_id)
    
    print(f"Agent ready! Thread ID: {thread_id}")
    print("Type '__CALL_STARTED__' to trigger greeting.")
    print("Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input("\nYou: ")
        except EOFError:
            break
            
        if user_input.lower() in ["exit", "quit"]:
            break
            
        print("Agent: ", end="", flush=True)
        stream = executor.astream(
            {"messages": [HumanMessage(content=user_input)]},
            {"configurable": {"thread_id": thread_id}},
            stream_mode="messages"
        )
        
        async for chunk, metadata in stream:
            # LangGraph can emit node names (str) or a list/dict of messages during streaming
            if isinstance(chunk, str):
                continue
            
            message = chunk
            if isinstance(chunk, dict):
                # Sometimes it emits the whole state update dict
                continue

            # Only listen to messages from our actual speech nodes
            valid_nodes = ["greeting", "profiling", "diagnostic", "advisory"]
            if not metadata or metadata.get("langgraph_node") not in valid_nodes:
                continue
                
            is_ai = hasattr(message, 'content') and 'ai' in message.type.lower()
            if is_ai and message.content:
                # Filter out tools
                is_tool = getattr(message, "tool_calls", None) or getattr(message, "tool_call_chunks", None)
                if getattr(message, "chunk", None) == False: 
                    continue # deduplicate final message prints if it streams chunks
                if not is_tool:
                    print(message.content, end="", flush=True)
            
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tc in message.tool_calls:
                    print(f"\n[Tool Call: {tc['name']}({tc['args']})]")
        print()

if __name__ == "__main__":
    asyncio.run(main())
