from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from datetime import datetime, timezone
from db.base import Base

class Advisory(Base):
    __tablename__ = "advisories"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    advisory_text_hindi = Column(Text, nullable=False)
    advisory_text_english = Column(Text)
    immediate_action = Column(Text)
    next_48_hours = Column(Text)
    preventive_measures = Column(Text)
    kb_entry_ids = Column(Text)
    was_escalated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))