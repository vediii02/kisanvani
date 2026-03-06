from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.session import get_db
from db.base import AsyncSessionLocal
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
        from openai import AsyncOpenAI
        from db.models.knowledge_base import KnowledgeEntry
        from db.session import get_db
        from sqlalchemy import select
        
        # 1. Convert query to embedding using OpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await client.embeddings.create(
            input=request.query,
            model="text-embedding-3-small",
        )
        query_embedding = response.data[0].embedding
        
        # 2. Search in Postgres using pgvector
        async with AsyncSessionLocal() as db_session:
            # We use a broad search here, but ideally should be scoped by organization
            # For backward compatibility with the Qdrant endpoint which was org-specific
            # we'll try to find any relevant entries.
            stmt = (
                select(KnowledgeEntry)
                .order_by(KnowledgeEntry.embedding.cosine_distance(query_embedding))
                .limit(request.limit)
            )
            result = await db_session.execute(stmt)
            results = result.scalars().all()
        
        if not results:
            return KBQueryResponse(
                query=request.query,
                answer="क्षमा करें, इस सवाल के बारे में knowledge base में जानकारी नहीं मिली।",
                sources=[]
            )
        
        # 3. Build context from results
        context = "\n\n".join([
            (doc.content or "")[:500] 
            for doc in results
        ])
        
        # Step 4: Generate answer using configured LLM provider
        prompt = f"""आप एक expert कृषि सलाहकार हैं। नीचे दिए गए knowledge base के आधार पर किसान के सवाल का सटीक और helpful जवाब दें।

Knowledge Base:
{context}

किसान का सवाल: {request.query}

जवाब (2-3 वाक्यों में, clear और practical):"""

        from services.config_service import get_platform_config
        config = await get_platform_config()
        llm_provider = config.get("llm_model", "groq")

        if llm_provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {'role': 'system', 'content': 'आप एक expert कृषि सलाहकार हैं।'},
                    {'role': 'user', 'content': prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
        else:
            from groq import Groq
            client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            response = client.chat.completions.create(
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
                'disease': getattr(doc, 'problem_type', 'Unknown'),
                'topic': getattr(doc, 'crop', 'Unknown'),
                'score': 0.0 # Score not directly available from simple scalar selection
            }
            for doc in results
        ]
        
        return KBQueryResponse(
            query=request.query,
            answer=answer,
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")