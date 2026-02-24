from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

QDRANT_URL = "http://kisanvani_qdrant:6333"
COLLECTION = "agri_advisories"
VECTOR_SIZE = 384  # For MiniLM-L12-v2

def create_collection():
    client = QdrantClient(QDRANT_URL)
    if COLLECTION not in [c.name for c in client.get_collections().collections]:
        client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"Collection '{COLLECTION}' created.")
    else:
        print(f"Collection '{COLLECTION}' already exists.")

# Example usage:
# create_collection()
