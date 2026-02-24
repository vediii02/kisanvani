"""
Index kb_entries into Qdrant vector database using local embeddings
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from db.models.kb_entry import KBEntry
from core.config import settings
from rag.retriever import RAGRetriever

async def index_kb_entries():
    """Index all approved kb_entries into Qdrant"""
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            print("🔍 Fetching kb_entries from database...")
            
            # Get all approved entries
            result = await session.execute(
                select(KBEntry).where(
                    KBEntry.is_approved == True,
                    KBEntry.is_banned == False
                )
            )
            entries = result.scalars().all()
            
            if not entries:
                print("❌ No approved kb_entries found in database")
                return
            
            print(f"✅ Found {len(entries)} approved entries")
            
            # Initialize RAG retriever
            print(f"🚀 Connecting to Qdrant at {settings.QDRANT_URL}...")
            rag = RAGRetriever(settings.QDRANT_URL, settings.QDRANT_COLLECTION)
            print("✅ Connected to Qdrant")
            
            # Index each entry
            print("\n📊 Indexing entries into Qdrant...")
            for idx, entry in enumerate(entries, 1):
                # Create searchable text by combining relevant fields
                searchable_text = f"{entry.title}\n\n{entry.content}"
                if entry.tags:
                    searchable_text += f"\n\nTags: {entry.tags}"
                
                # Metadata to store with vector
                metadata = {
                    "kb_id": entry.id,
                    "title": entry.title,
                    "content": entry.content,
                    "crop_name": entry.crop_name or "",
                    "problem_type": entry.problem_type or "",
                    "solution_steps": entry.solution_steps or "",
                    "tags": entry.tags or "",
                    "language": entry.language or "hi"
                }
                
                # Add to Qdrant
                rag.add_kb_entry(
                    kb_id=entry.id,
                    text=searchable_text,
                    metadata=metadata
                )
                
                print(f"  {idx}/{len(entries)} ✓ Indexed: {entry.title[:60]}...")
            
            print(f"\n🎉 Successfully indexed {len(entries)} entries into Qdrant!")
            print("\n📋 Indexed entries:")
            for entry in entries:
                print(f"  • ID {entry.id}: {entry.title}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(index_kb_entries())
