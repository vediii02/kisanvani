from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rag_pipeline.RAG_BOT.rag_service import run_rag_chat

router = APIRouter(tags=["RAG"])


class RagRequest(BaseModel):
    query: str


class RagResponse(BaseModel):
    answer: str


@router.post("/generate-response", response_model=RagResponse)
def generate_rag_response(payload: RagRequest):

    try:
        answer = run_rag_chat(payload.query)
        return {"answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))