# db/models/organisation_phone.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base

class OrganisationPhoneNumber(Base):
    """
    Critical table for multi-tenant call routing.
    
    Business Rule: Phone number is the SINGLE SOURCE OF TRUTH for organisation identification.
    When a farmer calls, we use 'to_phone' (the number they dialed) to identify which 
    organisation's AI should respond.
    
    Key Constraints:
    - One phone number can belong to ONLY ONE organisation (unique constraint)
    - One organisation can have MULTIPLE phone numbers (one-to-many)
    - Without an active phone number, organisation cannot receive calls
    """
    __tablename__ = "organisation_phone_numbers"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to organisations table - WHO owns this number
    organisation_id = Column(Integer, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # The actual phone number - THIS IS THE ROUTING KEY
    # Format: Must be standardized (e.g., +91xxxxxxxxxx or just digits)
    # This is what farmers will dial to reach this organisation
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Channel type - currently only 'voice' but future-proof for SMS, WhatsApp
    channel = Column(String(20), default="voice", nullable=False)  # voice, whatsapp, sms
    
    # Active status - If false, calls to this number will be rejected
    # Organisation admin can toggle this to temporarily disable a number
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Optional: Geographic area/region this number serves
    # Example: "Maharashtra", "Punjab", "All India"
    # Useful for regional product recommendations or language preferences
    region = Column(String(100), nullable=True)
    
    # Display name for this number (optional)
    # Example: "Main Helpline", "Punjab Regional Office"
    display_name = Column(String(100), nullable=True)
    
    # Audit fields
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationship back to organisation
    organisation = relationship("Organisation", back_populates="phone_numbers_rel")
    
    # Composite index for fast lookups during call routing
    # Most common query: "SELECT * FROM organisation_phone_numbers WHERE phone_number = ? AND is_active = true"
    __table_args__ = (
        Index('idx_phone_active_lookup', 'phone_number', 'is_active'),
    )
    
    def __repr__(self):
        return f"<OrganisationPhone(id={self.id}, org_id={self.organisation_id}, number={self.phone_number}, active={self.is_active})>"

