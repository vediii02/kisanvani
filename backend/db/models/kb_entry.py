from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
import sqlalchemy as sa
from datetime import datetime, timezone
from db.base import Base

class KBEntry(Base):
    __tablename__ = "kb_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    organisation_id = Column(Integer, sa.ForeignKey('organisations.id'), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    crop_name = Column(String(100))
    problem_type = Column(String(100))
    solution_steps = Column(Text)
    tags = Column(Text)
    is_approved = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    language = Column(String(10), default='hi')
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))