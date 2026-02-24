from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base
import enum

class CallStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class CallSession(Base):
    __tablename__ = "call_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    farmer_id = Column(Integer, ForeignKey('farmers.id'), nullable=True)
    phone_number = Column(String(15), nullable=False)
    provider_name = Column(String(50))
    provider_call_id = Column(String(200))
    status = Column(SQLEnum(CallStatus), default=CallStatus.ACTIVE)
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # New columns from migration
    from_phone = Column(String(20), nullable=True)
    to_phone = Column(String(20), nullable=True)
    exotel_call_sid = Column(String(100), nullable=True)
    call_direction = Column(SQLEnum('inbound', 'outbound', name='call_direction_enum'), default='inbound')
    
    # Advisory fields (added for RAG advisory tracking)
    advisory_generated = Column(Integer, default=0, nullable=False)
    advisory_text = Column(Text, nullable=True)
    raw_advisory = Column(Text, nullable=True)
    # Relationships (commented out to avoid circular import issues)
    # Will be accessed via queries instead
    # states = relationship("CallState", back_populates="call_session", cascade="all, delete-orphan")
    # transcripts = relationship("CallTranscript", back_populates="call_session", cascade="all, delete-orphan")
    # metrics = relationship("CallMetrics", back_populates="call_session", uselist=False)
    # summary = relationship("CallSummary", back_populates="call_session", uselist=False)