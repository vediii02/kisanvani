# db/models/company.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base

class Company(Base):
    """
    Company Model - Part of multi-tenant hierarchy
    Organisation → Company → Operators/Products
    
    Each organisation can have multiple companies.
    Each company has its own isolated dashboard.
    """
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    organisation_id = Column(Integer, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Company Details
    name = Column(String(200), nullable=False)
    business_type = Column(String(100), nullable=True)  # Retailer, Distributor, Manufacturer, etc.
    brand_name = Column(String(200), nullable=True)  # Optional brand/trading name
    
    # Contact Information
    contact_person = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    
    # Business Details
    gst_number = Column(String(50), nullable=True)
    registration_number = Column(String(100), nullable=True)
    
    # Status & Limits
    status = Column(String(50), default="active")  # active, inactive, suspended
    max_operators = Column(Integer, default=5)  # Max operators allowed for this company
    max_products = Column(Integer, default=100)  # Max products allowed
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )
    
    # Relationships
    # One company belongs to one organisation
    # One company has many operators (users with company_id)
    # One company has many products
