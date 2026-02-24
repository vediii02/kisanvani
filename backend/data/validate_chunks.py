#!/usr/bin/env python3
"""
Test script to verify wheat_rust_chunks.py structure
without requiring OpenAI API
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from wheat_rust_chunks import wheat_rust_chunks

def validate_chunks():
    """Validate chunk structure"""
    print("="*80)
    print("WHEAT RUST CHUNKS - VALIDATION")
    print("="*80)
    
    required_fields = ['crop', 'disease_type', 'topic', 'content', 'source']
    
    print(f"\nTotal chunks: {len(wheat_rust_chunks)}")
    
    # Validate structure
    errors = []
    for i, chunk in enumerate(wheat_rust_chunks):
        for field in required_fields:
            if field not in chunk:
                errors.append(f"Chunk {i}: Missing field '{field}'")
            elif not chunk[field]:
                errors.append(f"Chunk {i}: Empty field '{field}'")
    
    if errors:
        print("\n❌ Validation errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ All chunks have valid structure")
    
    # Statistics
    print("\nStatistics:")
    print(f"  - Total chunks: {len(wheat_rust_chunks)}")
    
    # By disease type
    disease_counts = {}
    for chunk in wheat_rust_chunks:
        disease = chunk['disease_type']
        disease_counts[disease] = disease_counts.get(disease, 0) + 1
    
    print("\n  Disease types:")
    for disease, count in sorted(disease_counts.items()):
        print(f"    - {disease}: {count} chunks")
    
    # By topic
    topic_counts = {}
    for chunk in wheat_rust_chunks:
        topic = chunk['topic']
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    print("\n  Topics:")
    for topic, count in sorted(topic_counts.items()):
        print(f"    - {topic}: {count} chunks")
    
    # Content length stats
    lengths = [len(chunk['content']) for chunk in wheat_rust_chunks]
    avg_length = sum(lengths) / len(lengths)
    min_length = min(lengths)
    max_length = max(lengths)
    
    print(f"\n  Content length:")
    print(f"    - Average: {avg_length:.0f} characters")
    print(f"    - Min: {min_length} characters")
    print(f"    - Max: {max_length} characters")
    
    # Sample chunk
    print("\n  Sample chunk (first one):")
    sample = wheat_rust_chunks[0]
    print(f"    - Crop: {sample['crop']}")
    print(f"    - Disease: {sample['disease_type']}")
    print(f"    - Topic: {sample['topic']}")
    print(f"    - Content preview: {sample['content'][:100]}...")
    print(f"    - Source: {sample['source']}")
    
    print("\n" + "="*80)
    print("✅ Validation complete - chunks are ready for embedding!")
    print("="*80)
    
    return True


if __name__ == "__main__":
    success = validate_chunks()
    sys.exit(0 if success else 1)
