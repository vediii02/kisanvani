from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from db.models.kb_entry import KBEntry
from db.models.organisation import Organisation
from schemas.kb import KBEntryResponse
from typing import List
import csv
import io
# import PyPDF2

router = APIRouter(prefix="/kb", tags=["knowledge_base"])

@router.post("/upload", response_model=List[KBEntryResponse])
async def upload_kb_file(
    organisation_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Validate organisation
    org = await db.get(Organisation, organisation_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    entries = []
    if file.filename.endswith('.csv'):
        content = await file.read()
        reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        for row in reader:
            entry = KBEntry(
                organisation_id=organisation_id,
                title=row.get('title', ''),
                content=row.get('content', ''),
                crop_name=row.get('crop_name'),
                problem_type=row.get('problem_type'),
                solution_steps=row.get('solution_steps'),
                tags=row.get('tags'),
                language=row.get('language', 'hi'),
                is_approved=True
            )
            db.add(entry)
            entries.append(entry)
        await db.commit()
        for entry in entries:
            await db.refresh(entry)
    elif file.filename.endswith('.pdf'):
        content = await file.read()
        pdf = PyPDF2.PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        # For demo: treat each paragraph as a KB entry
        for para in text.split('\n\n'):
            if para.strip():
                entry = KBEntry(
                    organisation_id=organisation_id,
                    title=para[:60],
                    content=para,
                    language='hi',
                    is_approved=True
                )
                db.add(entry)
                entries.append(entry)
        await db.commit()
        for entry in entries:
            await db.refresh(entry)
    else:
        raise HTTPException(status_code=400, detail="Only CSV and PDF supported")
    return entries
