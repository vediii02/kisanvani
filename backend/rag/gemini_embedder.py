"""
Production Gemini Embeddings using Google Generative AI
"""

import google.generativeai as genai
from typing import List
import logging
import os

logger = logging.getLogger(__name__)


class GeminiEmbedder:
    """
    Generate embeddings using Google Gemini API
    Production ready with proper error handling
    """
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini with API key"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        genai.configure(api_key=self.api_key)
        self.model_name = "models/text-embedding-004"
        self.dimension = 768  # Gemini embedding dimension
        logger.info(f"✅ Gemini embeddings initialized (dim={self.dimension})")
    
    def encode(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not text or not text.strip():
            return [0.0] * self.dimension
        
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Gemini embedding error: {str(e)}")
            raise
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        embeddings = []
        for text in texts:
            embeddings.append(self.encode(text))
        return embeddings


# Global instance
_embedder_instance = None


def get_gemini_embedder() -> GeminiEmbedder:
    """Get or create Gemini embedder instance"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = GeminiEmbedder()
    return _embedder_instance
