from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from datetime import datetime, timezone
from db.base import Base
import enum

class CaseStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('call_sessions.id'), nullable=False)
    farmer_id = Column(Integer, ForeignKey('farmers.id'), nullable=False)
    problem_text = Column(Text, nullable=False)
    problem_category = Column(String(100))
    crop_name = Column(String(100))
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.OPEN)
    confidence_score = Column(String(10))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))