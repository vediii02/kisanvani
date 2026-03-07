# db/models/user.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=True)

    hashed_password = Column(String(500), nullable=False)

    full_name = Column(String(200))
    role = Column(String(50), default="company")  # admin, organisation, company
    organisation_id = Column(Integer, ForeignKey("organisations.id", ondelete="SET NULL"), nullable=True)  # For organisation role
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)  # For company role
    status = Column(String(20), default="active")  # active, inactive, rejected, pending
    reset_token = Column(String(500), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships - FK points to org/company (many-to-one), no cascade needed here
    # Deletion of user's org/company when user is deleted is handled in the delete endpoint
    organisation = relationship("Organisation", foreign_keys=[organisation_id], back_populates="users")
    company = relationship("Company", foreign_keys=[company_id], back_populates="users")
