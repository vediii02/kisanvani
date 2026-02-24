from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CaseBase(BaseModel):
    problem_text: str
    problem_category: Optional[str] = None
    crop_name: Optional[str] = None

class CaseCreate(CaseBase):
    session_id: int
    farmer_id: int

class CaseResponse(CaseBase):
    id: int
    session_id: int
    farmer_id: int
    status: str
    confidence_score: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True