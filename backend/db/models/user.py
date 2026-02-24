# db/models/user.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime, timezone
from db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=True)

    hashed_password = Column(String(500), nullable=False)

    full_name = Column(String(200))
    role = Column(String(50), default="operator")  # admin, organisation, company, operator
    organisation_id = Column(Integer, ForeignKey("organisations.id"), nullable=True)  # For organisation role
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)  # For company and operator roles
    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
