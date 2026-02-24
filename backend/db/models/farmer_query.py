from sqlalchemy import Column, BigInteger, Text, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from db.base import Base

class FarmerQuery(Base):
    __tablename__ = "farmer_queries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    call_session_id = Column(BigInteger, ForeignKey("call_sessions.id"), nullable=False)
    farmer_id = Column(BigInteger, ForeignKey("farmers.id"), nullable=True)
    organisation_id = Column(BigInteger, ForeignKey("organisations.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_call_session_id", "call_session_id"),
        Index("ix_farmer_id", "farmer_id"),
        Index("ix_organisation_id", "organisation_id"),
    )
