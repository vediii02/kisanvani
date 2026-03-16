import asyncio
import os
import sys

# Ensure current directory is in sys.path to find backend modules
sys.path.append(os.getcwd())

from services.voice.llm import (
    diagnose_problem, 
    suggest_products, 
    retrieve_context, 
    update_farmer_profile, 
    complete_diagnosis, 
    end_call
)
from services.voice.session_context import (
    set_current_organisation_id, 
    set_current_company_id, 
    set_current_phone_number, 
    set_current_farmer_row_id
)

async def test_all_tools():
    # 1. Setup Mock Context
    # Using org_id 1 and a dummy phone
    set_current_organisation_id(1)
    set_current_company_id(None)
    set_current_phone_number("1234567890")
    set_current_farmer_row_id(1) # Assuming a farmer with ID 1 exists for testing
    
    print("--- 🛠️ Starting Voice Tools Multi-Tool Test ---")

    # --- Tool 1: update_farmer_profile ---
    print("\n[Tool: update_farmer_profile]")
    try:
        res = await update_farmer_profile.ainvoke({
            "name": "Testing Ayush",
            "village": "Vidisha",
            "crop_type": "Soybean"
        })
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

    # --- Tool 2: diagnose_problem (ChromaDB) ---
    print("\n[Tool: diagnose_problem]")
    try:
        # Test 1: Global Search
        print("Testing Global Search...")
        res = await diagnose_problem.ainvoke({"query": "soybean leaf yellowing symptoms"})
        print(f"Global Result (first 100 chars): {res[:100]}...")

        # Test 2: Targeted Search
        print("\nTesting Targeted Search (Crop: soyabean)...")
        res = await diagnose_problem.ainvoke({"query": "soybean leaf yellowing symptoms", "crop": "soyabean"})
        print(f"Targeted Result (first 100 chars): {res[:100]}...")
    except Exception as e:
        print(f"Error: {e}")

    # --- Tool 3: retrieve_context (pgvector treatment search) ---
    print("\n[Tool: retrieve_context]")
    try:
        res = await retrieve_context.ainvoke({"query": "tomato early blight treatment"})
        print(f"Result (first 200 chars): {res[:200]}...")
    except Exception as e:
        print(f"Error: {e}")

    # --- Tool 4: suggest_products (pgvector product search) ---
    print("\n[Tool: suggest_products]")
    try:
        res = await suggest_products.ainvoke({"problem": "Blight", "crop": "Tomato"})
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

    # --- Tool 5: complete_diagnosis ---
    print("\n[Tool: complete_diagnosis]")
    try:
        res = await complete_diagnosis.ainvoke({"diagnosis": "Late Blight in Tomato"})
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

    # --- Tool 6: end_call ---
    print("\n[Tool: end_call]")
    try:
        res = await end_call.ainvoke({})
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_tools())
