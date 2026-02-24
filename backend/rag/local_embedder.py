"""
Local Embedding Generator using sentence-transformers
Works offline without OpenAI API
"""

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
import logging

logger = logging.getLogger(__name__)


class LocalEmbedder:
    """
    Generate embeddings using local multilingual sentence-transformer model
    Supports Hindi, English, and many other languages
    """
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize local embedding model
        This model supports 50+ languages including Hindi and English
        Embedding dimension: 384
        """
        logger.info(f"Loading local embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # MiniLM outputs 384-dimensional embeddings
        logger.info(f"✅ Local embedding model loaded (dim={self.dimension})")
    
    def encode(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        """
        if not text or not text.strip():
            return [0.0] * self.dimension
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (faster batch processing)
        """
        if not texts:
            return []
        
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()


# Global instance (singleton)
_embedder_instance = None


def get_embedder() -> LocalEmbedder:
    """Get or create embedder instance"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = LocalEmbedder()
    return _embedder_instance
