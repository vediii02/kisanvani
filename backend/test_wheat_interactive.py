#!/usr/bin/env python3
"""
Interactive Wheat Knowledge Base Query Tool
अपना सवाल पूछो और AI से answer पाओ
"""

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from groq import Groq
import os
import sys

GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
BOLD = '\033[1m'
NC = '\033[0m'

print(f"\n{CYAN}{BOLD}{'='*70}{NC}")
print(f"{CYAN}{BOLD}🌾 WHEAT KNOWLEDGE BASE - Interactive Q&A 🌾{NC}")
print(f"{CYAN}{BOLD}{'='*70}{NC}\n")

# Initialize
print(f"{BLUE}⚙️  Loading AI models...{NC}")
qdrant = QdrantClient(url="http://qdrant:6333")
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
print(f"{GREEN}✅ Ready!\n{NC}")

def query_wheat_kb(question):
    """Query wheat knowledge base and get AI answer"""
    
    print(f"\n{YELLOW}Processing your question...{NC}\n")
    
    # Step 1: Embedding
    print(f"{BLUE}[1/3] Converting to vector...{NC}")
    vector = model.encode(question).tolist()
    
    # Step 2: Search
    print(f"{BLUE}[2/3] Searching knowledge base...{NC}")
    results = qdrant.query_points(
        collection_name="org_2_wheat_kb",
        query=vector,
        limit=3
    ).points
    
    if not results:
        print(f"{YELLOW}⚠️  No relevant information found{NC}")
        return
    
    print(f"{GREEN}✓ Found {len(results)} relevant documents{NC}\n")
    
    # Show sources
    print(f"{CYAN}📚 Sources used:{NC}")
    for i, r in enumerate(results, 1):
        disease = r.payload.get('disease', 'Unknown')
        topic = r.payload.get('topic', 'Unknown')
        print(f"   {i}. {disease} - {topic}")
    
    # Build context
    context = "\n\n".join([r.payload.get('content', '') for r in results[:3]])
    
    # Step 3: Generate answer
    print(f"\n{BLUE}[3/3] Generating answer...{NC}\n")
    
    prompt = f"""Knowledge Base से जानकारी:
{context}

Farmer का सवाल: {question}

Expert की तरह सटीक और practical जवाब दो (2-3 lines):"""

    response = groq.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[
            {'role': 'system', 'content': 'आप गेहूं के रोगों के expert हैं।'},
            {'role': 'user', 'content': prompt}
        ],
        max_tokens=200
    )
    
    answer = response.choices[0].message.content.strip()
    
    # Display
    print(f"{GREEN}{BOLD}💬 AI Answer:{NC}")
    print(f"{GREEN}{answer}{NC}\n")

# Main
if len(sys.argv) > 1:
    # Command line argument
    question = ' '.join(sys.argv[1:])
    query_wheat_kb(question)
else:
    # Interactive mode
    print(f"{YELLOW}Examples:{NC}")
    print(f"  • गेहूं में रतुआ रोग के लक्षण क्या हैं?")
    print(f"  • तना रतुआ का इलाज कैसे करें?")
    print(f"  • रतुआ रोग की दवाई कौन सी है?\n")
    
    while True:
        try:
            question = input(f"{CYAN}{BOLD}❓ Your Question (or 'exit' to quit): {NC}").strip()
            
            if question.lower() in ['exit', 'quit', 'q']:
                print(f"\n{GREEN}धन्यवाद! Goodbye! 🙏{NC}\n")
                break
            
            if not question:
                continue
            
            query_wheat_kb(question)
            
        except KeyboardInterrupt:
            print(f"\n\n{GREEN}Goodbye! 🙏{NC}\n")
            break
        except Exception as e:
            print(f"\n{YELLOW}Error: {e}{NC}\n")
