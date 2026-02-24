import os
import glob
from datetime import datetime
import asyncio
from sqlalchemy import select
from db.models.kb_entry import KBEntry
from db.base import AsyncSessionLocal

# Crop type mapping
CROP_MAP = {
    'गेहूं': 'wheat',
    'चना': 'gram',
    'धान': 'rice',
    'मक्का': 'maize',
}

CHUNK_SIZE = 600
OVERLAP = 100
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), 'knowledge_pdfs')


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += chunk_size - overlap
    return chunks


def get_title(chunk):
    # Use first non-empty line as title, else auto-generate
    for line in chunk.splitlines():
        line = line.strip()
        if line:
            return line[:60]
    return 'कृषि ज्ञान'



async def main():
    async with AsyncSessionLocal() as session:
        for filepath in glob.glob(os.path.join(KNOWLEDGE_DIR, '*.txt')):
            filename = os.path.basename(filepath)
            crop_key = filename.replace('.txt', '')
            crop_type = CROP_MAP.get(crop_key, None)
            if not crop_type:
                print(f"Skipping unknown crop file: {filename}")
                continue
            with open(filepath, encoding='utf-8') as f:
                text = f.read()
            chunks = chunk_text(text)
            for chunk in chunks:
                title = get_title(chunk)
                # Check for duplicate content
                result = await session.execute(
                    select(KBEntry).where(KBEntry.content == chunk)
                )
                exists = result.scalar_one_or_none()
                if exists:
                    continue
                entry = KBEntry(
                    title=title,
                    content=chunk,
                    crop_name=crop_type,
                    language='hi',
                    is_approved=True,
                    created_at=datetime.utcnow()
                )
                session.add(entry)
            await session.commit()
    print("Knowledge ingestion complete.")

if __name__ == '__main__':
    asyncio.run(main())
