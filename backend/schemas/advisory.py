from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AdvisoryBase(BaseModel):
    advisory_text_hindi: str
    advisory_text_english: Optional[str] = None
    immediate_action: Optional[str] = None
    next_48_hours: Optional[str] = None
    preventive_measures: Optional[str] = None

class AdvisoryCreate(AdvisoryBase):
    case_id: int
    kb_entry_ids: Optional[str] = None
    was_escalated: bool = False

class AdvisoryResponse(AdvisoryBase):
    id: int
    case_id: int
    was_escalated: bool
    created_at: datetime

    class Config:
        from_attributes = True