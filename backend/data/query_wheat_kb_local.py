#!/usr/bin/env python3
"""
Query Wheat Rust Knowledge Base using LOCAL embeddings (FREE)
Demo script to test semantic search with sentence-transformers
"""

import sys
from typing import List, Dict
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Configuration
QDRANT_URL = "http://qdrant:6333"
COLLECTION_NAME = "org_2_wheat_kb"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class WheatKBQuery:
    """Query wheat rust knowledge base"""
    
    def __init__(self):
        self.qdrant = QdrantClient(url=QDRANT_URL, prefer_grpc=False)
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print("✅ Model loaded\n")
    
    def query(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant chunks"""
        # Check collection exists
        collections = self.qdrant.get_collections().collections
        if COLLECTION_NAME not in [c.name for c in collections]:
            print(f"❌ Collection '{COLLECTION_NAME}' not found!")
            print("Please run load_wheat_kb_to_qdrant.py first")
            sys.exit(1)
        
        # Create query embedding
        query_vector = self.embedding_model.encode(query_text).tolist()
        
        # Search using query_points
        results = self.qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )
        
        return results.points
    
    def display_results(self, query: str, results):
        """Display search results"""
        print("="*80)
        print(f"Query: {query}")
        print("="*80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{'='*80}")
            print(f"Result {i} - Score: {result.score:.4f}")
            print(f"{'='*80}")
            print(f"Disease: {result.payload['disease_type']}")
            print(f"Topic: {result.payload['topic']}")
            print(f"Crop: {result.payload['crop']}")
            print(f"\nContent:")
            print("-"*80)
            print(result.payload['content'])
            print("-"*80)
        
        print(f"\n{'='*80}\n")


def main():
    """Run demo queries"""
    queryer = WheatKBQuery()
    
    # Demo queries
    demo_queries = [
        "गेहूँ में तना रतुआ के लक्षण क्या हैं?",
        "पीला रतुआ का रासायनिक नियंत्रण कैसे करें?",
        "भूरा रतुआ के लिए कौन से फफूंदीनाशक प्रभावी हैं?"
    ]
    
    # Check if custom query provided
    if len(sys.argv) > 1:
        custom_query = " ".join(sys.argv[1:])
        print(f"Custom Query: {custom_query}\n")
        results = queryer.query(custom_query, top_k=3)
        queryer.display_results(custom_query, results)
    else:
        # Run demo queries
        print("Running Demo Queries...")
        print("="*80)
        
        for query in demo_queries:
            results = queryer.query(query, top_k=2)
            queryer.display_results(query, results)
            input("\nPress Enter for next query...")


if __name__ == "__main__":
    main()
