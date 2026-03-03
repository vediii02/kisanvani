import os
import logging
from openai import AsyncOpenAI
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.knowledge_base import KnowledgeEntry
from db.models.product import Product

logger = logging.getLogger("kb_sync")

# Unique source prefix to link KB entries back to their parent Product
_SOURCE_PREFIX = "product_sync:"


def _build_source_tag(product_id: int) -> str:
    return f"{_SOURCE_PREFIX}{product_id}"


def _build_product_content(product: Product) -> str:
    brand_str = f" manufactured by {product.brand.name}" if getattr(product, 'brand', None) else ""
    return (
        f"Product Name: {product.name}{brand_str}.\n"
        f"Category: {product.category}, Sub-Category: {product.sub_category}.\n"
        f"Description: {product.description}\n"
        f"Target Crops: {product.target_crops}\n"
        f"Target Problems/Diseases/Pests: {product.target_problems}\n"
        f"Dosage Requirements: {product.dosage}\n"
        f"Usage Instructions: {product.usage_instructions}\n"
        f"Safety Precautions: {product.safety_precautions}\n"
        f"Price Range: {product.price_range}"
    ).strip()


async def _generate_embedding(content: str) -> list[float] | None:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_KEY")
    if not api_key:
        logger.warning("No OpenAI API key found, skipping embedding generation")
        return None
    client = AsyncOpenAI(api_key=api_key)
    response = await client.embeddings.create(input=content, model="text-embedding-3-small")
    return response.data[0].embedding


async def sync_product_to_kb(product: Product, db: AsyncSession):
    """
    Create or Update: Upserts the product into knowledge_entries.
    Uses source='product_sync:{id}' to find existing entries.
    """
    source_tag = _build_source_tag(product.id)
    content = _build_product_content(product)

    try:
        embedding = await _generate_embedding(content)
        if embedding is None:
            return

        # Check if a KB entry already exists for this product
        result = await db.execute(
            select(KnowledgeEntry).where(KnowledgeEntry.source == source_tag)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # UPDATE existing entry
            existing.content = content
            existing.embedding = embedding
            existing.crop = str(product.target_crops)[:100]
            existing.problem_type = str(product.category)[:50]
            existing.organisation_id = product.organisation_id
            existing.company_id = product.company_id
            logger.info(f"Updated KB entry for product '{product.name}' (ID: {product.id})")
        else:
            # CREATE new entry
            entry = KnowledgeEntry(
                organisation_id=product.organisation_id,
                company_id=product.company_id,
                crop=str(product.target_crops)[:100],
                problem_type=str(product.category)[:50],
                source=source_tag,
                content=content,
                embedding=embedding
            )
            db.add(entry)
            logger.info(f"Created KB entry for product '{product.name}' (ID: {product.id})")

    except Exception as e:
        logger.error(f"Failed to sync product '{product.name}' to KB: {e}")


async def delete_product_from_kb(product_id: int, db: AsyncSession):
    """
    Delete: Removes the KB entry linked to a specific product.
    """
    source_tag = _build_source_tag(product_id)
    try:
        await db.execute(
            delete(KnowledgeEntry).where(KnowledgeEntry.source == source_tag)
        )
        logger.info(f"Deleted KB entry for product ID: {product_id}")
    except Exception as e:
        logger.error(f"Failed to delete KB entry for product ID {product_id}: {e}")
