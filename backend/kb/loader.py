from sqlalchemy.ext.asyncio import AsyncSession
from db.models.kb_entry import KBEntry
from rag.gemini_retriever import GeminiRAGRetriever
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class KBLoader:
    def __init__(self):
        self.rag = None
    
    def _get_rag(self):
        if self.rag is None:
            self.rag = GeminiRAGRetriever(settings.QDRANT_URL, settings.QDRANT_COLLECTION)
        return self.rag
    
    async def load_entry_to_vector_db(self, kb_entry: KBEntry):
        if not kb_entry.is_approved or kb_entry.is_banned:
            logger.warning(f"Skipping KB entry {kb_entry.id} - not approved or banned")
            return
        
        metadata = {
            'kb_id': kb_entry.id,
            'title': kb_entry.title,
            'content': kb_entry.content,
            'crop_name': kb_entry.crop_name,
            'problem_type': kb_entry.problem_type,
            'tags': kb_entry.tags,
        }
        
        combined_text = f"{kb_entry.title} {kb_entry.content}"
        rag = self._get_rag()
        rag.add_kb_entry(kb_entry.id, combined_text, metadata)
        logger.info(f"Loaded KB entry {kb_entry.id} to vector DB")

kb_loader = KBLoader()