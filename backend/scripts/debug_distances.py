import asyncio
import os
import sys
from sqlalchemy import select, func

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from services.voice.llm import fetch_embedding
from db.base import AsyncSessionLocal
from db.models.knowledge_base import KnowledgeEntry

async def debug_distances():
    query = "treatment for worms in paddy"
    print(f"--- Query: {query} ---")
    
    vec = await fetch_embedding(query)
    print(f"Embedding vector length: {len(vec)}")
    
    async with AsyncSessionLocal() as db:
        # Get all entries and their distances
        stmt = select(
            KnowledgeEntry.id,
            KnowledgeEntry.crop,
            KnowledgeEntry.problem_type,
            KnowledgeEntry.embedding.cosine_distance(vec).label("distance")
        ).order_by("distance")
        
        result = await db.execute(stmt)
        rows = result.all()
        
        print("\nTop 5 Distances:")
        for row in rows[:5]:
            print(f"ID: {row.id} | Crop: {row.crop} | Problem: {row.problem_type} | Distance: {row.distance:.4f}")

if __name__ == "__main__":
    asyncio.run(debug_distances())
