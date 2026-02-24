from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base

class OrganisationKnowledgeBase(Base):
    __tablename__ = "organisation_kb_files"

    id = Column(Integer, primary_key=True, index=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id'), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf or csv
    file_path = Column(String(500), nullable=False)
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="pending")  # pending, processed, failed
    error_message = Column(Text, nullable=True)

    organisation = relationship("Organisation", backref="kb_files")
