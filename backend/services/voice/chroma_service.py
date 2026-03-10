import os
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
COLLECTION_NAME = "crop_diagnostics"

class ChromaService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaService, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance
    
    def _init_service(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=CHROMA_DB_DIR
        )
        
    async def query_diagnostics(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Query ChromaDB for relevant crop diagnostic information."""
        try:
            # Note: langchain-chroma's asearch is not always available in all versions, 
            # using synchronous similarity_search_with_score for reliability.
            results = self.vector_store.similarity_search_with_score(query, k=limit)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            return formatted_results
        except Exception as e:
            print(f"Chroma query failed: {e}")
            return []

# Singleton instance
chroma_service = ChromaService()
