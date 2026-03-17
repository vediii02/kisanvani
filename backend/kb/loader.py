import os
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import AsyncOpenAI

from db.base import AsyncSessionLocal
from db.models.kb_entry import KBEntry
from db.models.knowledge_base import KnowledgeEntry
from db.models.product import Product
from services.voice.llm import fetch_embedding

logger = logging.getLogger(__name__)

class KBLoader:
    def __init__(self):
        pass
    
    async def load_entry_to_vector_db(self, kb_entry: KBEntry):
        """Generates embedding and saves it to knowledge_entries table."""
        if not kb_entry.is_approved or kb_entry.is_banned:
            logger.warning(f"Skipping KB entry {kb_entry.id} - not approved or banned")
            return

        try:
            # Construct a comprehensive text representation
            content_parts = [
                f"Title: {kb_entry.title}",
                f"Crop: {kb_entry.crop_name or 'N/A'}",
                f"Problem Type: {kb_entry.problem_type or 'N/A'}",
                f"Description: {kb_entry.content}",
                f"Solution: {kb_entry.solution_steps or 'N/A'}",
                f"Tags: {kb_entry.tags or 'N/A'}"
            ]
            embed_text = "\n".join([p for p in content_parts if p])
            full_content_text = f"Title: {kb_entry.title}\n{kb_entry.content}\nSolution: {kb_entry.solution_steps or ''}"

            logger.info(f"Generating embedding for KB entry {kb_entry.id}")
            embedding_vector = await fetch_embedding(embed_text)
            source_id = f"kb_entry:{kb_entry.id}"

            async with AsyncSessionLocal() as db:
                # Find existing KnowledgeEntry if it exists
                stmt = select(KnowledgeEntry).where(KnowledgeEntry.source == source_id)
                result = await db.execute(stmt)
                knowledge_entry = result.scalar_one_or_none()
                
                if knowledge_entry:
                    # Update existing
                    knowledge_entry.organisation_id = kb_entry.organisation_id
                    knowledge_entry.crop = kb_entry.crop_name
                    knowledge_entry.problem_type = kb_entry.problem_type
                    knowledge_entry.content = full_content_text
                    knowledge_entry.embedding = embedding_vector
                    
                    # We commit to save changes.
                    await db.commit()
                    logger.info(f"Updated existing KnowledgeEntry for kb_entry {kb_entry.id}")
                else:
                    # Create new
                    knowledge_entry = KnowledgeEntry(
                        organisation_id=kb_entry.organisation_id,
                        company_id=None,
                        crop=kb_entry.crop_name,
                        problem_type=kb_entry.problem_type,
                        source=source_id,
                        content=full_content_text,
                        embedding=embedding_vector
                    )
                    db.add(knowledge_entry)
                    await db.commit()
                    logger.info(f"Created new KnowledgeEntry with embedding for kb_entry {kb_entry.id}")

        except Exception as e:
            logger.error(f"Error generating or saving embedding for kb_entry {kb_entry.id}: {e}")

    async def load_product_to_vector_db(self, product: Product):
        """Generates embedding for a product and saves it to knowledge_entries table."""
        source_id = f"product:{product.id}"
        
        if getattr(product, 'is_active', True) is False:
            logger.info(f"Product {product.id} is inactive. Removing from KB if exists.")
            async with AsyncSessionLocal() as db:
                from sqlalchemy import delete
                await db.execute(delete(KnowledgeEntry).where(KnowledgeEntry.source == source_id))
                await db.commit()
            return

        try:
            # Construct a comprehensive text representation
            content_parts = [
                f"Product Name: {product.name}",
                f"Category: {product.category}",
                f"Description: {getattr(product, 'description', '') or ''}",
                f"Target Crops: {getattr(product, 'target_crops', '') or ''}",
                f"Target Problems: {getattr(product, 'target_problems', '') or ''}",
                f"Dosage: {getattr(product, 'dosage', '') or ''}",
                f"Usage Instructions: {getattr(product, 'usage_instructions', '') or ''}"
            ]
            embed_text = "\n".join([p for p in content_parts if ": " in p and p.split(': ')[1].strip()])
            
            # Combine info for the 'content' field that the AI reads
            summary_content = "\n".join(content_parts)

            logger.info(f"Generating embedding for Product {product.id} ({product.name})")
            embedding_vector = await fetch_embedding(embed_text)
            source_id = f"product:{product.id}"

            async with AsyncSessionLocal() as db:
                # Find existing KnowledgeEntry if it exists
                stmt = select(KnowledgeEntry).where(KnowledgeEntry.source == source_id)
                result = await db.execute(stmt)
                knowledge_entry = result.scalar_one_or_none()
                
                if knowledge_entry:
                    # Update existing
                    knowledge_entry.organisation_id = product.organisation_id
                    knowledge_entry.company_id = product.company_id
                    knowledge_entry.crop = getattr(product, 'target_crops', '')
                    knowledge_entry.problem_type = getattr(product, 'target_problems', '')
                    knowledge_entry.content = summary_content
                    knowledge_entry.embedding = embedding_vector
                    knowledge_entry.metadata_ = {
                        "brand_id": getattr(product, 'brand_id', None),
                        "category": product.category,
                        "sub_category": getattr(product, 'sub_category', None),
                        "price": getattr(product, 'price', None),
                        "price_range": getattr(product, 'price_range', None)
                    }
                    knowledge_entry.language = 'hi'  # Default for this platform
                    
                    await db.commit()
                    logger.info(f"Updated existing KnowledgeEntry for product {product.id}")
                else:
                    # Create new
                    knowledge_entry = KnowledgeEntry(
                        organisation_id=product.organisation_id,
                        company_id=product.company_id,
                        crop=getattr(product, 'target_crops', ''),
                        problem_type=getattr(product, 'target_problems', ''),
                        source=source_id,
                        content=summary_content,
                        embedding=embedding_vector,
                        metadata_={
                            "brand_id": getattr(product, 'brand_id', None),
                            "category": product.category,
                            "sub_category": getattr(product, 'sub_category', None),
                            "price": getattr(product, 'price', None),
                            "price_range": getattr(product, 'price_range', None)
                        },
                        language='hi'
                    )
                    db.add(knowledge_entry)
                    await db.commit()
                    logger.info(f"Created new KnowledgeEntry with embedding for product {product.id}")

        except Exception as e:
            logger.error(f"Error generating or saving embedding for product {product.id}: {e}")

kb_loader = KBLoader()
