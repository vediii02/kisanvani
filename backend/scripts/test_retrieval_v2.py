import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from services.voice.llm import retrieve_context
from services.voice.session_context import set_current_organisation_id

async def test_retrieval():
    print("--- Testing RAG Retrieval Tool ---")
    
    # Ensure env is loaded or manually set
    os.environ["VOICE_DEFAULT_ORGANISATION_ID"] = "1"
    
    test_queries = [
        "Mere kapas ki fasal ke patte peele ho rahe hain", # Cotton leaves turning yellow
        "paddy pest control",
        "wheat rust treatment"
    ]
    
    print("\n1. Testing with EXPLICIT org_id=1")
    res = await retrieve_context.ainvoke({"query": test_queries[0], "organisation_id": 1})
    print(f"Result length: {len(res)}")
    print(f"Content preview: {res[:200]}...")
    
    print("\n2. Testing with NO org_id (should fallback to env/hardcoded)")
    set_current_organisation_id(None)
    res = await retrieve_context.ainvoke({"query": test_queries[1]})
    print(f"Result length: {len(res)}")
    print(f"Content preview: {res[:200]}...")
    
    print("\n3. Testing with WRONG org_id (should return no information)")
    res = await retrieve_context.ainvoke({"query": test_queries[2], "organisation_id": 999})
    print(f"Result: {res}")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
