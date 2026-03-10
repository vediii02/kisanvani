import asyncio
import os
import sys
from sqlalchemy import select

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from db.base import AsyncSessionLocal
from db.models.kb_entry import KBEntry
from db.models.product import Product
from kb.loader import kb_loader

async def reindex_all():
    async with AsyncSessionLocal() as db:
        # 1. Re-index KB Entries
        kb_entries = (await db.execute(select(KBEntry))).scalars().all()
        print(f"Found {len(kb_entries)} KB entries to re-index")
        for entry in kb_entries:
            print(f"Re-indexing KB Entry {entry.id}: {entry.title}")
            await kb_loader.load_entry_to_vector_db(entry)
            
        # 2. Re-index Products
        products = (await db.execute(select(Product))).scalars().all()
        print(f"Found {len(products)} products to re-index")
        for prod in products:
            print(f"Re-indexing Product {prod.id}: {prod.name}")
            await kb_loader.load_product_to_vector_db(prod)
            
    print("\nRe-indexing Complete!")

if __name__ == "__main__":
    asyncio.run(reindex_all())
