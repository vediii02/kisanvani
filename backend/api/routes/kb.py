from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.session import get_db
from db.models.kb_entry import KBEntry
from schemas.kb import KBEntryCreate, KBEntryUpdate, KBEntryResponse
from kb.loader import kb_loader
from typing import List
from pydantic import BaseModel
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kb", tags=["knowledge_base"])

# Query Models
class KBQueryRequest(BaseModel):
    query: str
    language: str = "hi"
    limit: int = 3

class KBQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[dict]

@router.post("/entries", response_model=KBEntryResponse)
async def create_kb_entry(
    entry: KBEntryCreate,
    db: AsyncSession = Depends(get_db)
):
    kb_entry = KBEntry(**entry.model_dump())
    db.add(kb_entry)
    await db.commit()
    await db.refresh(kb_entry)
    
    await kb_loader.load_entry_to_vector_db(kb_entry)
    
    logger.info(f"Created KB entry {kb_entry.id}")
    return kb_entry

@router.get("/entries", response_model=List[KBEntryResponse])
async def get_kb_entries(
    skip: int = 0,
    limit: int = 100,
    approved_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    query = select(KBEntry)
    if approved_only:
        query = query.where(KBEntry.is_approved == True, KBEntry.is_banned == False)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/entries/{entry_id}", response_model=KBEntryResponse)
async def get_kb_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(KBEntry).where(KBEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="KB entry not found")
    return entry

@router.put("/entries/{entry_id}", response_model=KBEntryResponse)
async def update_kb_entry(
    entry_id: int,
    entry_update: KBEntryUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(KBEntry).where(KBEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="KB entry not found")
    
    for key, value in entry_update.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    
    await db.commit()
    await db.refresh(entry)
    
    await kb_loader.load_entry_to_vector_db(entry)
    
    return entry

@router.delete("/entries/{entry_id}")
async def delete_kb_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(KBEntry).where(KBEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="KB entry not found")
    
    await db.delete(entry)
    await db.commit()
    
    return {'message': 'KB entry deleted', 'id': entry_id}

@router.post("/query", response_model=KBQueryResponse)
async def query_knowledge_base(request: KBQueryRequest):
    """Query the wheat knowledge base using RAG pipeline"""
    try:
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        from groq import Groq
        
        # Initialize
        qdrant = QdrantClient(url="http://qdrant:6333")
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        # Step 1: Convert query to embedding
        query_vector = model.encode(request.query).tolist()
        
        # Step 2: Search in Qdrant
        results = qdrant.query_points(
            collection_name="org_2_wheat_kb",
            query=query_vector,
            limit=request.limit
        ).points
        
        if not results:
            return KBQueryResponse(
                query=request.query,
                answer="क्षमा करें, इस सवाल के बारे में knowledge base में जानकारी नहीं मिली।",
                sources=[]
            )
        
        # Step 3: Build context from results
        context = "\n\n".join([
            result.payload.get('content', '')[:500] 
            for result in results
        ])
        
        # Step 4: Generate answer with Groq
        prompt = f"""आप एक expert कृषि सलाहकार हैं। नीचे दिए गए knowledge base के आधार पर किसान के सवाल का सटीक और helpful जवाब दें।

Knowledge Base:
{context}

किसान का सवाल: {request.query}

जवाब (2-3 वाक्यों में, clear और practical):"""

        response = groq.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content': 'आप एक expert कृषि सलाहकार हैं।'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=250,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Prepare sources
        sources = [
            {
                'disease': result.payload.get('disease', 'Unknown'),
                'topic': result.payload.get('topic', 'Unknown'),
                'score': float(result.score)
            }
            for result in results
        ]
        
        return KBQueryResponse(
            query=request.query,
            answer=answer,
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")