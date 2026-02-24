from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
from rag.local_embedder import get_embedder
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class RAGRetriever:
    def __init__(self, qdrant_url: str, collection_name: str):
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        # Use local multilingual embeddings
        self.embedder = get_embedder()
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' exists")
        except Exception:
            logger.info(f"Creating collection '{self.collection_name}'")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # MiniLM embedding dimension
                    distance=Distance.COSINE
                ),
            )

    def add_kb_entry(self, kb_id: int, text: str, metadata: Dict[str, Any]):
        # Use local embeddings
        vector = self.embedder.encode(text)
        point = PointStruct(
            id=kb_id,
            vector=vector,
            payload=metadata,
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        # Use local embeddings
        query_vector = self.embedder.encode(query)

        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[],
            query=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
        )

        points = response.points or []

        return [
            {
                "id": p.id,
                "score": p.score,
                "metadata": p.payload,
            }
            for p in points
        ]

def retrieve_chunks(question, top_k=5):
    QDRANT_URL = "http://kisanvani_qdrant:6333"
    COLLECTION = "agri_advisories"
    EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    model = SentenceTransformer(EMBED_MODEL)
    client = QdrantClient(QDRANT_URL)
    q_emb = model.encode(question).tolist()
    hits = client.search(
        collection_name=COLLECTION,
        query_vector=q_emb,
        limit=top_k
    )
    return [hit.payload["text"] for hit in hits], hits
