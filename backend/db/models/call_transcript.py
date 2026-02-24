"""Call transcripts model"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from db.base import Base
from datetime import datetime
import enum


class Speaker(str, enum.Enum):
    """Who spoke"""
    AI = "AI"
    FARMER = "FARMER"
    EXPERT = "EXPERT"


class CallTranscript(Base):
    __tablename__ = "call_transcripts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_session_id = Column(Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False)
    speaker = Column(SQLEnum(Speaker), nullable=False)
    transcript_text = Column(Text, nullable=False)
    language_code = Column(String(10), default="hi-IN")
    audio_duration_ms = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)  # STT confidence
    spoken_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships (commented out to avoid circular import)
    # call_session = relationship("CallSession", back_populates="transcripts")
    
    # Indexes
    __table_args__ = (
        Index('idx_transcripts_call', 'call_session_id'),
        Index('idx_transcripts_speaker', 'speaker'),
    )
    
    def __repr__(self):
        return f"<CallTranscript(id={self.id}, speaker={self.speaker.value}, text={self.transcript_text[:50]}...)>"
