"""
Production RAG Retriever using Gemini Embeddings
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
from rag.gemini_embedder import get_gemini_embedder
import logging

logger = logging.getLogger(__name__)


class GeminiRAGRetriever:
    """Production RAG with Gemini embeddings"""
    
    def __init__(self, qdrant_url: str, collection_name: str):
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self.embedder = get_gemini_embedder()
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
                    size=768,  # Gemini embedding dimension
                    distance=Distance.COSINE
                ),
            )

    def add_kb_entry(self, kb_id: int, text: str, metadata: Dict[str, Any]):
        """Add knowledge base entry with Gemini embedding"""
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
        """Search knowledge base using Gemini embeddings"""
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
