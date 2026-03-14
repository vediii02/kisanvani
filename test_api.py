import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(base_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from db.base import AsyncSessionLocal
from db.models.knowledge_base import KnowledgeEntry
from services.voice.llm import fetch_embedding

app = FastAPI(title="KisanVani Standalone Product Search API")

class ProductSearchRequest(BaseModel):
    problem: str
    crop: str | None = None
    limit: int = 5

class ProductSearchResponse(BaseModel):
    advice: str
    product_count: int

async def pyvector_similarity_search(problem: str, crop: str | None = None, limit: int = 5) -> tuple[str, int]:
    query_text = f"{crop or ''} {problem}".strip()
    
    try:
        query_vector = await fetch_embedding(query_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating search query embedding: {e}")

    async with AsyncSessionLocal() as db:
        distance_col = KnowledgeEntry.embedding.cosine_distance(query_vector)
        stmt = (
            select(KnowledgeEntry)
            .where(KnowledgeEntry.source.like("product:%"))
            .order_by(distance_col)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        entries = result.scalars().all()
        
    if not entries:
        return f"No specific products found for '{problem}' in '{crop or 'this crop'}'.", 0
    
    advice = "Available Products:\n"
    for entry in entries:
        advice += f"---\n{entry.content}\n"
        
    return advice, len(entries)

@app.post("/api/search-products")
async def search_products_api(request: Request):
    try:
        data = await request.json()
        print("RECEIVED DATA:", data)
    except Exception as e:
        print("ERROR PARSING JSON:", e)
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # If Retell didn't use 'args only', the arguments are nested under 'args'
    if "args" in data:
        args = data.get("args", {})
        problem = args.get("problem")
        crop = args.get("crop")
    else:
        problem = data.get("problem")
        crop = data.get("crop")

    limit = data.get("limit", 5)

    if not problem:
        raise HTTPException(status_code=422, detail="Field required: problem")

    advice, count = await pyvector_similarity_search(problem, crop, limit)
    return ProductSearchResponse(advice=advice, product_count=count)

if __name__ == "__main__":
    import uvicorn
    print("Starting Product API server on http://0.0.0.0:8005")
    uvicorn.run("test_api:app", host="0.0.0.0", port=8005, reload=True)
