from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base

class FarmerQuestion(Base):
    __tablename__ = "farmer_questions"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    call_sid = Column(String(64), nullable=False)
    organisation_id = Column(Integer, ForeignKey("organisations.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    answered_at = Column(DateTime(timezone=True), nullable=True)

    farmer = relationship("Farmer", backref="questions")
