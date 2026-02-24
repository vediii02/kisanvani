"""Call state model"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from db.base import Base
from datetime import datetime
import enum


class StateType(str, enum.Enum):
    """Call flow states"""
    INCOMING = "INCOMING"
    GREETING = "GREETING"
    PROFILING = "PROFILING"
    PROBLEM = "PROBLEM"
    ADVISORY = "ADVISORY"
    ESCALATED = "ESCALATED"
    CLOSURE = "CLOSURE"
    ENDED = "ENDED"


class CallState(Base):
    __tablename__ = "call_states"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_session_id = Column(Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False)
    state = Column(SQLEnum(StateType), nullable=False)
    entered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    exited_at = Column(DateTime, nullable=True)
    state_data = Column(JSON, nullable=True)  # State-specific context
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships (commented out to avoid circular import)
    # call_session = relationship("CallSession", back_populates="states")
    
    # Indexes
    __table_args__ = (
        Index('idx_call_states_session', 'call_session_id'),
        Index('idx_call_states_state', 'state'),
    )
    
    def __repr__(self):
        return f"<CallState(id={self.id}, call={self.call_session_id}, state={self.state.value})>"
