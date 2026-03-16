import asyncio
import os
import chromadb
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

from services.voice.logger import setup_logger
logger = setup_logger("chroma")

CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")

class ChromaService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaService, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance
    
    def _init_service(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        # PersistentClient allows listing collections
        self.client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        
    async def query_diagnostics(self, query: str, limit: int = 5, crop: str | None = None) -> List[Dict[str, Any]]:
        """Query ChromaDB for relevant information, optionally targeting a specific crop collection."""
        try:
            target_collection = None
            if crop:
                # Sanitize crop name exactly like the ingestion script
                clean_crop = "".join([c if c.isalnum() or c in ("_", "-") else "_" for c in crop.lower()])
                clean_crop = clean_crop.strip("_").strip("-")
                
                # Check if this specific collection exists (case-insensitive for robustness)
                collections = await asyncio.to_thread(self.client.list_collections)
                collection_names = [coll.name if hasattr(coll, "name") else str(coll) for coll in collections]
                
                if clean_crop in collection_names:
                    target_collection = clean_crop
                else:
                    for coll_name in collection_names:
                        if coll_name.lower() == clean_crop:
                            target_collection = coll_name
                            break
                
                if target_collection:
                    logger.info("Targeted Chroma search in collection: %s", target_collection)
                else:
                    logger.info("No specific collection found for crop '%s', falling back to global search.", crop)

            all_results = []
            
            if target_collection:
                # Targeted search in one collection
                vector_store = Chroma(
                    client=self.client,
                    collection_name=target_collection,
                    embedding_function=self.embeddings
                )
                results = await asyncio.to_thread(
                    vector_store.similarity_search_with_score, query, k=limit
                )
                for doc, score in results:
                    all_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": float(score)
                    })
            else:
                # Global search across all collections
                collections = await asyncio.to_thread(self.client.list_collections)
                if not collections:
                    return []
                
                async def _search_collection(coll_name):
                    vector_store = Chroma(
                        client=self.client,
                        collection_name=coll_name,
                        embedding_function=self.embeddings
                    )
                    return await asyncio.to_thread(
                        vector_store.similarity_search_with_score, query, k=limit
                    )

                search_tasks = []
                for coll in collections:
                    coll_name = coll.name if hasattr(coll, "name") else str(coll)
                    search_tasks.append(_search_collection(coll_name))
                
                results_batches = await asyncio.gather(*search_tasks)
                for batch in results_batches:
                    for doc, score in batch:
                        all_results.append({
                            "content": doc.page_content,
                            "metadata": doc.metadata,
                            "score": float(score)
                        })
                
                # Sort by score (lower is better)
                all_results.sort(key=lambda x: x["score"])
            
            return all_results[:limit]
            
        except Exception as e:
            print(f"Chroma multi-collection query failed: {e}")
            import traceback
            traceback.print_exc()
            return []

# Singleton instance
chroma_service = ChromaService()
