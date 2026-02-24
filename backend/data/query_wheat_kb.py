#!/usr/bin/env python3
"""
Query Wheat Rust Knowledge Base
Demo script to test RAG retrieval
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from openai import AsyncOpenAI

# Load environment
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "org_2_wheat_kb"
EMBEDDING_MODEL = "text-embedding-3-small"


async def query_knowledge_base(query: str, top_k: int = 3):
    """Query the wheat rust knowledge base"""
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found")
        sys.exit(1)
    
    # Initialize clients
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    openai_client = AsyncOpenAI()
    
    # Check if collection exists
    try:
        collections = qdrant.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if COLLECTION_NAME not in collection_names:
            print(f"❌ Collection '{COLLECTION_NAME}' not found")
            print("Please run load_wheat_kb_to_qdrant.py first")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        sys.exit(1)
    
    print("="*80)
    print(f"Query: {query}")
    print("="*80)
    
    # Create query embedding
    print("\n⏳ Creating query embedding...")
    try:
        response = await openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query
        )
        query_vector = response.data[0].embedding
        print("✅ Embedding created")
    except Exception as e:
        print(f"❌ Error creating embedding: {e}")
        sys.exit(1)
    
    # Search Qdrant
    print(f"\n🔍 Searching for top {top_k} results...")
    try:
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True
        )
        print(f"✅ Found {len(results)} results\n")
    except Exception as e:
        print(f"❌ Error searching: {e}")
        sys.exit(1)
    
    # Display results
    for i, result in enumerate(results, 1):
        print(f"{'='*80}")
        print(f"Result {i} - Score: {result.score:.4f}")
        print(f"{'='*80}")
        print(f"फसल: {result.payload.get('crop')}")
        print(f"रोग: {result.payload.get('disease_type')}")
        print(f"विषय: {result.payload.get('topic')}")
        print(f"स्रोत: {result.payload.get('source')}")
        print(f"\nसामग्री:")
        print(result.payload.get('content'))
        print()
    
    return results


async def main():
    """Main entry point"""
    
    # Demo queries
    queries = [
        "गेहूँ में तना रतुआ के लक्षण क्या हैं?",
        "पीला रतुआ का रासायनिक नियंत्रण कैसे करें?",
        "भूरा रतुआ के लिए कौन से फफूंदीनाशक प्रभावी हैं?"
    ]
    
    if len(sys.argv) > 1:
        # Use query from command line
        query = " ".join(sys.argv[1:])
        await query_knowledge_base(query)
    else:
        # Run demo queries
        print("\n" + "="*80)
        print("WHEAT RUST KNOWLEDGE BASE - DEMO QUERIES")
        print("="*80)
        print("\nRunning 3 demo queries...\n")
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'#'*80}")
            print(f"DEMO QUERY {i}/{len(queries)}")
            print(f"{'#'*80}\n")
            
            await query_knowledge_base(query, top_k=2)
            
            if i < len(queries):
                print("\n" + "."*80 + "\n")
        
        print("\n" + "="*80)
        print("✅ Demo complete!")
        print("="*80)
        print("\nUsage: python3 query_wheat_kb.py <your query in Hindi>")
        print("Example: python3 query_wheat_kb.py गेहूँ में रतुआ रोग का उपचार")


if __name__ == "__main__":
    asyncio.run(main())
