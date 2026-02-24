from rag_pipeline.RAG_BOT.openai_client import get_embedding
from rag_pipeline.RAG_BOT.pinecone_db import get_index
from rag_pipeline.RAG_BOT.loader import load_file
# from chunker import chunk_text
import os

def chunk_text(text, chunk_size=1200, overlap=200):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

def ingest_file(file_path: str, company_id: int):
    """
    Ingest a file for a specific company namespace
    """

    # 1️⃣ Load file
    filename = os.path.basename(file_path)
    text = load_file(file_path, filename)

    # 2️⃣ Chunk
    chunks = chunk_text(text)

    # 3️⃣ Get index
    index = get_index()

    vectors = []

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)

        vectors.append({
            "id": f"{company_id}_{filename}_{i}",
            "values": embedding,
            "metadata": {
                "text": chunk,
                "source_file": filename
            }
        })

    # 4️⃣ Upsert into namespace
    index.upsert(
        vectors=vectors,
        namespace=str(company_id)  # 🔐 isolation
    )

    print(f"✅ Ingested {len(vectors)} chunks for {company_id}")


def delete_company_chunks(company_id: int):
    index = get_index()
    namespace = str(company_id)

    try:
        index.delete(
            delete_all=True,
            namespace=namespace
        )
        return True

    except Exception as e:
        # Log actual error
        print(f"Deletion error: {e}")
        return False