"""
Index kb_entries to Qdrant using Gemini embeddings - PRODUCTION
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from db.models.kb_entry import KBEntry
from core.config import settings
from rag.gemini_retriever import GeminiRAGRetriever

async def index_kb_entries():
    """Index all approved kb_entries into Qdrant using Gemini"""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            print("🔍 Fetching kb_entries from database...")
            
            result = await session.execute(
                select(KBEntry).where(
                    KBEntry.is_approved == True,
                    KBEntry.is_banned == False
                )
            )
            entries = result.scalars().all()
            
            if not entries:
                print("❌ No approved kb_entries found")
                return
            
            print(f"✅ Found {len(entries)} approved entries")
            
            print(f"🚀 Connecting to Qdrant with Gemini embeddings...")
            rag = GeminiRAGRetriever(settings.QDRANT_URL, settings.QDRANT_COLLECTION)
            print("✅ Connected")
            
            print("\n📊 Indexing with Gemini embeddings...")
            for idx, entry in enumerate(entries, 1):
                searchable_text = f"{entry.title}\n\n{entry.content}"
                if entry.tags:
                    searchable_text += f"\n\nTags: {entry.tags}"
                
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
                
                rag.add_kb_entry(
                    kb_id=entry.id,
                    text=searchable_text,
                    metadata=metadata
                )
                
                print(f"  {idx}/{len(entries)} ✓ {entry.title[:60]}...")
            
            print(f"\n🎉 Successfully indexed {len(entries)} entries with Gemini!")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(index_kb_entries())
