"""Call summary model for SMS/WhatsApp"""

from sqlalchemy import Column, Integer, Text, DateTime, JSON, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from db.base import Base
from datetime import datetime


class CallSummary(Base):
    __tablename__ = "call_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_session_id = Column(Integer, ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Summary content
    summary_text_hindi = Column(Text, nullable=False)
    summary_text_english = Column(Text, nullable=True)
    
    # Structured data
    key_recommendations = Column(JSON, nullable=True)  # ["recommendation 1", "recommendation 2"]
    products_mentioned = Column(JSON, nullable=True)  # [product_id_1, product_id_2]
    
    # Delivery tracking
    sms_sent = Column(Boolean, default=False)
    sms_sent_at = Column(DateTime, nullable=True)
    whatsapp_sent = Column(Boolean, default=False)
    whatsapp_sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships (commented out to avoid circular import)
    # call_session = relationship("CallSession", back_populates="summary")
    
    # Indexes
    __table_args__ = (
        Index('idx_call_summaries_call', 'call_session_id'),
    )
    
    def __repr__(self):
        return f"<CallSummary(id={self.id}, call={self.call_session_id}, sms={self.sms_sent})>"
