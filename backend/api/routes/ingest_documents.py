from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
import shutil
import logging
import uuid
from fastapi import Depends
from rag_pipeline.RAG_BOT.ingest import ingest_file ,delete_company_chunks # your ingest.py function
from core.permissions import require_role
from fastapi import HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])

UPLOAD_DIR = "temp_uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/file")
async def ingest_document(
    company_id: int = Form(...),
    file: UploadFile = File(...),
    current_user = Depends(require_role(["admin", "superadmin","company"])) 
):
    """
    Upload and ingest a document into Pinecone namespace
    """

    try:
        # 1️⃣ Create unique filename
        unique_filename = f"{uuid.uuid4()}_{file.filename}" 
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # 2️⃣ Save file temporarily
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3️⃣ Call ingestion
        ingest_file(file_path=file_path, company_id=company_id)

        # 4️⃣ Remove temp file (optional but recommended)
        os.remove(file_path)

        return {
            "status": "success",
            "message": f"File ingested successfully for company {company_id}"
        }

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )
    

@router.delete(
    "/company/{company_id}",
    dependencies=[Depends(require_role(["admin", "superadmin","delete"]))]
)
async def delete_company_data(company_id: int):
    deleted = delete_company_chunks(company_id)

    if not deleted:
        return {
            "status": "info",
            "message": f"No knowledge base found for company {company_id}"
        }

    return {
        "status": "success",
        "message": f"Knowledge base cleared for company {company_id}"
    }