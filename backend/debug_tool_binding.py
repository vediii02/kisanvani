
import asyncio
import os
import sys

# Add app to path
sys.path.append(os.getcwd())

from services.voice.llm import get_agent_executor, init_checkpointer, get_llm
from langchain_core.messages import HumanMessage, SystemMessage

async def debug_tools():
    await init_checkpointer()
    org_id = 2
    comp_id = 1
    
    # We call get_llm to see the raw model
    llm = await get_llm()
    print(f"LLM Provider: {type(llm)}")
    
    # Let's see the tools
    from services.voice.llm import update_farmer_profile, retrieve_context
    
    # When org_id is 2, the executor creates scoped tools
    # Let's recreate that logic briefly to inspect
    _update_farmer_profile_fn = update_farmer_profile.coroutine
    from langchain_core.tools import tool
    
    @tool("update_farmer_profile")
    async def update_farmer_profile_scoped(name: str = None, village: str = None):
        """Update farmer profile."""
        return "success"
        
    bound_llm = llm.bind_tools([update_farmer_profile_scoped])
    
    # Inspect the 'kwargs' where tools are stored in LangChain
    if hasattr(bound_llm, 'kwargs'):
        print(f"Bound Tools: {bound_llm.kwargs.get('tools')}")
    elif hasattr(bound_llm, 'additional_kwargs'):
        print(f"Additional Kwargs: {bound_llm.additional_kwargs}")
    
    # Try a direct invoke with explicit instructions
    messages = [
        SystemMessage(content="You must call 'update_farmer_profile' if you see a name."),
        HumanMessage(content="My name is Ramesh.")
    ]
    print("\nInvoking LLM directly...")
    resp = await bound_llm.ainvoke(messages)
    print(f"Response Type: {type(resp)}")
    print(f"Content: {resp.content}")
    print(f"Tool Calls: {getattr(resp, 'tool_calls', 'None')}")

if __name__ == "__main__":
    asyncio.run(debug_tools())
