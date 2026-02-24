#!/usr/bin/env python3
"""
Complete Integration Test for Kisan Vani AI
Tests: Vector DB, Embeddings, LLM, TTS, STT, RAG Pipeline
"""

import asyncio
import sys
import os

# Colors for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(text):
    print(f"\n{YELLOW}{'='*60}{NC}")
    print(f"{YELLOW}{text}{NC}")
    print(f"{YELLOW}{'='*60}{NC}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{NC}")

def print_error(text):
    print(f"{RED}❌ {text}{NC}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{NC}")

async def test_qdrant():
    """Test Qdrant Vector Database"""
    print_header("Test 1: Qdrant Vector Database")
    
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url="http://qdrant:6333")
        
        collections = client.get_collections()
        print_success(f"Connected to Qdrant")
        
        if collections.collections:
            for coll in collections.collections:
                info = client.get_collection(coll.name)
                print_success(f"Collection: {coll.name} - {info.points_count} vectors")
        else:
            print_info("No collections found - run load_wheat_kb_to_qdrant.py")
        
        return True
    except Exception as e:
        print_error(f"Qdrant test failed: {e}")
        return False

async def test_embeddings():
    """Test OpenAI Embeddings"""
    print_header("Test 2: OpenAI Embeddings (Vector Search)")
    
    try:
        from openai import OpenAI
        import os
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print_error("OPENAI_API_KEY not set")
            return False
        
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model='text-embedding-3-small',
            input='गेहूं की खेती कैसे करें'
        )
        
        embedding_dim = len(response.data[0].embedding)
        print_success(f"Embedding generated: {embedding_dim} dimensions")
        print_info(f"Model: text-embedding-3-small")
        return True
        
    except Exception as e:
        print_error(f"Embeddings test failed: {e}")
        return False

async def test_groq_llm():
    """Test Groq LLM"""
    print_header("Test 3: Groq LLM (AI Reasoning)")
    
    try:
        from groq import Groq
        import os
        
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print_error("GROQ_API_KEY not set")
            return False
        
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model='llama3-70b-8192',
            messages=[
                {'role': 'system', 'content': 'You are a helpful farming assistant.'},
                {'role': 'user', 'content': 'गेहूं में पीले पत्ते क्यों आते हैं? (Answer in 1 line)'}
            ],
            max_tokens=100
        )
        
        answer = response.choices[0].message.content.strip()
        print_success(f"LLM Response: {answer[:150]}...")
        print_info(f"Model: llama3-70b-8192")
        return True
        
    except Exception as e:
        print_error(f"Groq LLM test failed: {e}")
        return False

async def test_google_tts():
    """Test Google TTS"""
    print_header("Test 4: Google TTS (Text-to-Speech)")
    
    try:
        from voice.providers.google_tts import GoogleTTSProvider
        
        provider = GoogleTTSProvider()
        audio_data = await provider.synthesize('नमस्ते किसान भाई, आज का मौसम बहुत अच्छा है', 'hi')
        
        audio_size = len(audio_data)
        print_success(f"TTS audio generated: {audio_size} bytes")
        print_info(f"Provider: Google TTS (gTTS)")
        return True
        
    except Exception as e:
        print_error(f"Google TTS test failed: {e}")
        return False

async def test_rag_pipeline():
    """Test RAG Pipeline"""
    print_header("Test 5: RAG Pipeline (Complete Knowledge Retrieval)")
    
    try:
        from qdrant_client import QdrantClient
        from openai import OpenAI
        from groq import Groq
        import os
        
        # 1. Query embedding
        openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        query = "गेहूं में रतुआ रोग के लक्षण क्या हैं?"
        
        print_info(f"Query: {query}")
        
        # Get query embedding
        query_response = openai_client.embeddings.create(
            model='text-embedding-3-small',
            input=query
        )
        query_vector = query_response.data[0].embedding
        
        # 2. Vector search in Qdrant
        qdrant = QdrantClient(url="http://qdrant:6333")
        
        # Find collection (try different collection names)
        collections = qdrant.get_collections()
        if not collections.collections:
            print_error("No collections found in Qdrant")
            return False
        
        collection_name = collections.collections[0].name
        print_info(f"Searching in collection: {collection_name}")
        
        search_results = qdrant.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=3
        )
        
        if not search_results:
            print_error("No search results found")
            return False
        
        print_success(f"Found {len(search_results)} relevant documents")
        
        # 3. Build context from results
        context = "\n\n".join([
            result.payload.get('content', '') 
            for result in search_results[:3]
        ])
        
        # 4. Generate answer using Groq LLM
        groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        prompt = f"""आप एक कृषि सलाहकार हैं। नीचे दिए गए ज्ञान के आधार पर किसान के सवाल का जवाब दें।

ज्ञान:
{context}

सवाल: {query}

जवाब (2-3 वाक्य में):"""

        llm_response = groq_client.chat.completions.create(
            model='llama3-70b-8192',
            messages=[
                {'role': 'system', 'content': 'आप एक विशेषज्ञ कृषि सलाहकार हैं।'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=200
        )
        
        answer = llm_response.choices[0].message.content.strip()
        
        print_success("RAG Pipeline completed successfully!")
        print(f"\n{BLUE}📝 Final Answer:{NC}")
        print(f"{answer}\n")
        print_info(f"Sources used: {len(search_results)}")
        
        return True
        
    except Exception as e:
        print_error(f"RAG Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_redis_memory():
    """Test Redis Session Storage"""
    print_header("Test 6: Redis Memory (Session Storage)")
    
    try:
        import redis
        
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        # Test connection
        r.ping()
        print_success("Redis connected")
        
        # Test set/get
        test_key = "test:integration"
        r.set(test_key, "Hello from Kisan Vani AI", ex=60)
        value = r.get(test_key)
        
        print_success(f"Redis read/write: {value}")
        
        # Count sessions
        session_keys = r.keys("session:*")
        print_info(f"Active sessions: {len(session_keys)}")
        
        return True
        
    except Exception as e:
        print_error(f"Redis test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}🚀 Kisan Vani AI - Complete Integration Test{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    
    results = {}
    
    # Run tests
    results['Qdrant'] = await test_qdrant()
    results['Embeddings'] = await test_embeddings()
    results['Groq LLM'] = await test_groq_llm()
    results['Google TTS'] = await test_google_tts()
    results['RAG Pipeline'] = await test_rag_pipeline()
    results['Redis'] = await test_redis_memory()
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}✅ PASSED{NC}" if result else f"{RED}❌ FAILED{NC}"
        print(f"  {test_name:20} {status}")
    
    print(f"\n{BLUE}Total: {passed}/{total} tests passed{NC}\n")
    
    if passed == total:
        print(f"{GREEN}🎉 All systems integrated successfully!{NC}\n")
        return 0
    else:
        print(f"{YELLOW}⚠️  Some tests failed. Check the output above.{NC}\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
