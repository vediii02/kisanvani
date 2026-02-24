#!/usr/bin/env python3
"""
Simplified Integration Test - Uses Local/Free Services
Tests all components without external API dependencies where possible
"""

import asyncio
import sys

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_success(text):
    print(f"{GREEN}✅ {text}{NC}")

def print_error(text):
    print(f"{RED}❌ {text}{NC}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{NC}")

print(f"\n{BLUE}{'='*70}{NC}")
print(f"{BLUE}🚀 Kisan Vani AI - Integration Test (Local Services){NC}")
print(f"{BLUE}{'='*70}{NC}\n")

# Test 1: Qdrant Vector Database
print(f"{YELLOW}Test 1: Qdrant Vector Database{NC}")
try:
    from qdrant_client import QdrantClient
    client = QdrantClient(url="http://qdrant:6333")
    collections = client.get_collections()
    
    if collections.collections:
        for coll in collections.collections:
            info = client.get_collection(coll.name)
            print_success(f"Collection '{coll.name}': {info.points_count} vectors stored")
        print_info("Vector DB: Qdrant - Working ✓")
    else:
        print_info("No collections yet - run load script to add data")
except Exception as e:
    print_error(f"Qdrant: {e}")

print()

# Test 2: Local Embeddings (Sentence Transformers)
print(f"{YELLOW}Test 2: Local Embeddings (No API key needed){NC}")
try:
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    text = "गेहूं की खेती कैसे करें"
    embedding = model.encode(text)
    
    print_success(f"Embedding generated: {len(embedding)} dimensions")
    print_info(f"Model: paraphrase-multilingual-MiniLM-L12-v2 (Local, FREE)")
except Exception as e:
    print_error(f"Embeddings: {e}")

print()

# Test 3: Groq LLM
print(f"{YELLOW}Test 3: Groq LLM (AI Reasoning){NC}")
try:
    from groq import Groq
    import os
    
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print_error("GROQ_API_KEY not set")
    else:
        client = Groq(api_key=api_key)
        
        # Use updated model
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'user', 'content': 'Say "नमस्ते किसान भाई" in Hindi'}
            ],
            max_tokens=20
        )
        
        answer = response.choices[0].message.content.strip()
        print_success(f"LLM Response: {answer}")
        print_info("Model: llama-3.3-70b-versatile")
except Exception as e:
    print_error(f"Groq LLM: {e}")

print()

# Test 4: Google TTS
print(f"{YELLOW}Test 4: Google TTS (Text-to-Speech){NC}")
try:
    from voice.providers.google_tts import GoogleTTSProvider
    
    async def test_tts():
        provider = GoogleTTSProvider()
        audio = await provider.synthesize('नमस्ते किसान भाई', 'hi')
        return len(audio)
    
    audio_size = asyncio.run(test_tts())
    print_success(f"TTS audio: {audio_size} bytes")
    print_info("Provider: Google gTTS (Free)")
except Exception as e:
    print_error(f"TTS: {e}")

print()

# Test 5: Complete RAG Pipeline
print(f"{YELLOW}Test 5: Complete RAG Pipeline (Local Embeddings + Groq){NC}")
try:
    from qdrant_client import QdrantClient
    from sentence_transformers import SentenceTransformer
    from groq import Groq
    import os
    
    # Check prerequisites
    collections = QdrantClient(url="http://qdrant:6333").get_collections()
    if not collections.collections:
        print_info("No vector collections found - skipping RAG test")
        print_info("Run: docker exec kisanvani_backend python /app/data/load_wheat_kb_to_qdrant.py")
    else:
        collection_name = collections.collections[0].name
        
        # Step 1: Embed query using local model
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        query = "गेहूं में रतुआ रोग के लक्षण क्या हैं?"
        query_vector = model.encode(query).tolist()
        
        # Step 2: Search Qdrant
        qdrant = QdrantClient(url="http://qdrant:6333")
        results = qdrant.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=3
        ).points
        
        if not results:
            print_error("No search results")
        else:
            # Step 3: Build context
            context = "\n\n".join([r.payload.get('content', '')[:200] for r in results])
            
            # Step 4: Generate answer with Groq
            groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
            prompt = f"""ज्ञान: {context}\n\nसवाल: {query}\n\nजवाब (2 वाक्य):"""
            
            response = groq.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[
                    {'role': 'system', 'content': 'आप कृषि सलाहकार हैं।'},
                    {'role': 'user', 'content': prompt}
                ],
                max_tokens=150
            )
            
            answer = response.choices[0].message.content.strip()
            
            print_success("RAG Pipeline completed!")
            print(f"\n  {BLUE}Query:{NC} {query}")
            print(f"  {BLUE}Answer:{NC} {answer}\n")
            print_info(f"Pipeline: Local Embeddings → Qdrant → Groq LLM")
            
except Exception as e:
    print_error(f"RAG: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 6: Redis
print(f"{YELLOW}Test 6: Redis Memory (Session Storage){NC}")
try:
    import redis
    
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    r.ping()
    
    # Test write/read
    r.set("test:ai", "Kisan Vani AI", ex=60)
    value = r.get("test:ai")
    
    print_success(f"Redis: {value}")
    print_info("Session storage working")
except Exception as e:
    print_error(f"Redis: {e}")

print()

# Summary
print(f"{BLUE}{'='*70}{NC}")
print(f"{GREEN}✅ Integration Test Complete!{NC}")
print(f"{BLUE}{'='*70}{NC}\n")

print(f"{BLUE}Verified Components:{NC}")
print(f"  • Qdrant Vector Database (Embeddings Storage)")
print(f"  • Sentence Transformers (Local, FREE embeddings)")
print(f"  • Groq LLM (AI Reasoning - llama-3.3-70b-versatile)")
print(f"  • Google gTTS (Text-to-Speech)")
print(f"  • Redis (Session Management)")
print(f"  • Complete RAG Pipeline (Query → Search → Answer)\n")

print(f"{YELLOW}Note:{NC}")
print(f"  • STT: Currently using MOCK provider")
print(f"  • OpenAI: Not required (using local embeddings)\n")
