from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from pgvector.sqlalchemy import Vector
from datetime import datetime, timezone
from db.base import Base

class ConversationMemory(Base):
    __tablename__ = "conversation_memories"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(50), index=True, nullable=False)
    role = Column(String(20), nullable=False) # 'user' or 'ai' or 'system'
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True) # OpenAI vector size or whatever size is used
    metadata_json = Column(JSON, nullable=True) # Optional metadata like topic or intent
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
