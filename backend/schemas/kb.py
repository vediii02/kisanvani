from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KBEntryBase(BaseModel):
    title: str
    content: str
    crop_name: Optional[str] = None
    problem_type: Optional[str] = None
    solution_steps: Optional[str] = None
    tags: Optional[str] = None
    language: str = 'hi'
    organisation_id: Optional[int] = None

class KBEntryCreate(KBEntryBase):
    created_by: Optional[str] = 'system'

class KBEntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    crop_name: Optional[str] = None
    problem_type: Optional[str] = None
    solution_steps: Optional[str] = None
    tags: Optional[str] = None
    is_approved: Optional[bool] = None
    is_banned: Optional[bool] = None
    organisation_id: Optional[int] = None

class KBEntryResponse(KBEntryBase):
    id: int
    is_approved: bool
    is_banned: bool
    created_by: Optional[str] = None
    created_at: datetime
    organisation_id: Optional[int] = None

    class Config:
        from_attributes = True