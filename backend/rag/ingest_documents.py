import fitz  # PyMuPDF
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from sentence_transformers import SentenceTransformer
import uuid

QDRANT_URL = "http://kisanvani_qdrant:6333"
COLLECTION = "agri_advisories"
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def chunk_text(text, chunk_size=400):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def ingest_pdf(pdf_path, metadata):
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    model = SentenceTransformer(EMBED_MODEL)
    client = QdrantClient(QDRANT_URL)
    for chunk in chunks:
        embedding = model.encode(chunk).tolist()
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={**metadata, "text": chunk}
        )
        client.upsert(collection_name=COLLECTION, points=[point])

# Example usage:
# ingest_pdf("ICAR_wheat.pdf", metadata={"crop": "गेहूं", "source": "ICAR", "language": "hi"})
