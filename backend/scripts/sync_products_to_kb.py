#!/usr/bin/env python3
import sys
import os
import asyncio
import logging
from sqlalchemy import select, text

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.base import AsyncSessionLocal
from db.models.knowledge_base import KnowledgeEntry
from kb.loader import kb_loader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def sync_products_to_knowledge():
    """Syncs rows from 'products' and 'kb_entries' to 'knowledge_entries' with embeddings."""
    
    # 1. Fetch all products as dictionaries to avoid MissingGreenlet errors after rollbacks
    logger.info("Fetching products from database...")
    async with AsyncSessionLocal() as session:
        # Use a raw SQL or mapping select to get independent data
        result = await session.execute(text("SELECT * FROM products WHERE is_active = true"))
        products = [dict(row._mapping) for row in result.all()]
    
    logger.info(f"Syncing {len(products)} products...")
    
    for p in products:
        p_id = p['id']
        p_name = p['name']
        logger.info(f"Processing Product ID: {p_id} ({p_name})")
        
        async with AsyncSessionLocal() as session:
            try:
                content_parts = [
                    f"Product Name: {p_name}",
                    f"Category: {p.get('category','')}",
                    f"Description: {p.get('description','') or ''}",
                    f"Target Crops: {p.get('target_crops','') or ''}",
                    f"Target Problems: {p.get('target_problems','') or ''}",
                    f"Dosage: {p.get('dosage','') or ''}",
                    f"Usage Instructions: {p.get('usage_instructions','') or ''}"
                ]
                embed_text = "\n".join([cp for cp in content_parts if ": " in cp and cp.split(': ')[1]])
                
                logger.info(f"Generating embedding for product: {p_name}")
                client = kb_loader._get_openai_client()
                if not client:
                    logger.error("No OpenAI client available. Check OPENAI_API_KEY.")
                    return
                
                response = await client.embeddings.create(
                    input=embed_text,
                    model="text-embedding-3-small",
                )
                embedding_vector = response.data[0].embedding
                source_id = f"product:{p_id}"
                
                # Upsert into knowledge_entries
                kn_stmt = select(KnowledgeEntry).where(KnowledgeEntry.source == source_id)
                kn_result = await session.execute(kn_stmt)
                kn_entry = kn_result.scalar_one_or_none()
                
                summary_content = f"Product: {p_name}\nCategory: {p.get('category','')}\nCrops: {p.get('target_crops','')}\nProblems: {p.get('target_problems','')}\nDosage: {p.get('dosage','')}\nInstructions: {p.get('usage_instructions','')}"
                
                if kn_entry:
                    kn_entry.organisation_id = p.get('organisation_id')
                    kn_entry.company_id = p.get('company_id')
                    kn_entry.crop = p.get('target_crops','')
                    kn_entry.problem_type = p.get('target_problems','')
                    kn_entry.content = summary_content
                    kn_entry.embedding = embedding_vector
                    kn_entry.metadata_ = {
                        "brand_id": p.get('brand_id'),
                        "category": p.get('category'),
                        "sub_category": p.get('sub_category'),
                        "price": p.get('price'),
                        "price_range": p.get('price_range')
                    }
                    kn_entry.language = 'hi'
                    logger.info(f"Updated product entry in KB: {p_name}")
                else:
                    kn_entry = KnowledgeEntry(
                        organisation_id=p.get('organisation_id'),
                        company_id=p.get('company_id'),
                        crop=p.get('target_crops',''),
                        problem_type=p.get('target_problems',''),
                        source=source_id,
                        content=summary_content,
                        embedding=embedding_vector,
                        metadata_={
                            "brand_id": p.get('brand_id'),
                            "category": p.get('category'),
                            "sub_category": p.get('sub_category'),
                            "price": p.get('price'),
                            "price_range": p.get('price_range')
                        },
                        language='hi'
                    )
                    session.add(kn_entry)
                    logger.info(f"Created new product entry in KB: {p_name}")
                
                await session.commit()
                
            except Exception as e:
                logger.error(f"Error processing product {p_name} (ID: {p_id}): {e}")
                # We don't need explicit rollback here as session is in context manager scope 
                # but it helps to be explicit if we reuse it.
                await session.rollback()
                if "insufficient_quota" in str(e):
                    logger.error("Stopping sync due to OpenAI quota exhaustion.")
                    return

    # 2. Sync KB Entries
    logger.info("Fetching KB entries from database...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT id FROM kb_entries WHERE is_approved = true"))
        kb_ids = [row[0] for row in result.all()]
    
    from db.models.kb_entry import KBEntry
    for kb_id in kb_ids:
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(KBEntry).where(KBEntry.id == kb_id))
                kb_entry = result.scalar_one_or_none()
                if kb_entry:
                    logger.info(f"Processing KB Entry ID: {kb_id} ({kb_entry.title})")
                    await kb_loader.load_entry_to_vector_db(kb_entry)
            except Exception as e:
                logger.error(f"Error processing KB Entry {kb_id}: {e}")

    logger.info("Sync utility finished.")

if __name__ == "__main__":
    asyncio.run(sync_products_to_knowledge())
