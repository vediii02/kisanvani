# db/models/product.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from datetime import datetime, timezone
from db.base import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    organisation_id = Column(Integer, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)  # Products belong to companies
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)  # pesticide, fertilizer, seed, equipment
    sub_category = Column(String(100), nullable=True)  # insecticide, fungicide, herbicide, etc
    description = Column(Text, nullable=True)
    target_crops = Column(Text, nullable=True)  # JSON array
    target_problems = Column(Text, nullable=True)  # JSON array (pest names, diseases)
    dosage = Column(Text, nullable=True)
    usage_instructions = Column(Text, nullable=True)
    safety_precautions = Column(Text, nullable=True)
    price_range = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )
