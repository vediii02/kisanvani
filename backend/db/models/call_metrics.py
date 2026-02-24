"""Call metrics model for analytics"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Boolean, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from db.base import Base
from datetime import datetime
import enum


class CallOutcome(str, enum.Enum):
    """Final outcome of the call"""
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    ESCALATED = "ESCALATED"
    FAILED = "FAILED"
    CALLBACK_SCHEDULED = "CALLBACK_SCHEDULED"


class CallMetrics(Base):
    __tablename__ = "call_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_session_id = Column(Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False)
    organisation_id = Column(Integer, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False)
    
    # Duration tracking
    total_duration_seconds = Column(Integer, nullable=True)
    
    # Flow tracking
    states_visited = Column(JSON, nullable=True)  # ["GREETING", "PROFILING", ...]
    profiling_questions_completed = Column(Integer, default=0)
    
    # Problem understanding
    symptoms_detected = Column(Integer, default=0)
    
    # RAG metrics
    kb_entries_retrieved = Column(Integer, default=0)
    advisory_confidence = Column(Float, nullable=True)
    
    # Escalation
    was_escalated = Column(Boolean, default=False)
    escalation_reason = Column(String(255), nullable=True)
    
    # Feedback
    farmer_satisfaction = Column(Integer, nullable=True)  # 1-5 stars
    
    # Outcome
    call_outcome = Column(SQLEnum(CallOutcome), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships (commented out to avoid circular import)
    # call_session = relationship("CallSession", back_populates="metrics")
    # organisation = relationship("Organisation")
    
    # Indexes
    __table_args__ = (
        Index('idx_call_metrics_call', 'call_session_id'),
        Index('idx_call_metrics_org', 'organisation_id'),
        Index('idx_call_metrics_outcome', 'call_outcome'),
    )
    
    def __repr__(self):
        return f"<CallMetrics(id={self.id}, call={self.call_session_id}, outcome={self.call_outcome})>"
