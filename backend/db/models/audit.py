"""
Audit Log Model for Platform-wide Compliance
Tracks all critical changes made by Super Admin and other privileged users
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Date, text
from datetime import datetime, timezone
from db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Who did it
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    user_role = Column(String(50), nullable=False)
    
    # What was done
    action_type = Column(String(100), nullable=False, index=True)  # org_status_change, product_ban, kb_approval, etc.
    action_category = Column(String(50), nullable=False, index=True)  # organisation, product, kb, user, call, config
    description = Column(Text, nullable=False)
    
    # Where (which entity)
    entity_type = Column(String(50), nullable=True)  # organisation, user, product, kb_entry
    entity_id = Column(Integer, nullable=True, index=True)
    organisation_id = Column(Integer, nullable=True, index=True)  # For filtering by org
    
    # Before and After states
    old_value = Column(JSON, nullable=True)  # Previous state
    new_value = Column(JSON, nullable=True)  # New state
    
    # Additional context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    severity = Column(String(20), default="info")  # info, warning, critical
    
    # Timestamp
    timestamp = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True
    )
    
    # Additional context data
    extra_data = Column(JSON, nullable=True)


class PlatformConfig(Base):
    """
    Platform-level configuration that only Super Admin can change
    """
    __tablename__ = "platform_config"
    
    id = Column(Integer, primary_key=True)
    
    # AI Configuration
    ai_confidence_threshold = Column(Integer, default=70)  # 0-100
    max_call_duration_minutes = Column(Integer, default=15)
    default_language = Column(String(10), default="hi")
    
    # Provider Configuration
    stt_provider = Column(String(50), default="bhashini")  # bhashini, google
    tts_provider = Column(String(50), default="bhashini")
    llm_model = Column(String(100), default="gpt-4")
    
    # RAG Configuration
    rag_strictness_level = Column(String(20), default="medium")  # low, medium, high, strict
    rag_min_confidence = Column(Integer, default=60)
    rag_max_results = Column(Integer, default=5)
    
    # Safety & Compliance
    force_kb_approval = Column(Boolean, default=True)
    enable_call_recording = Column(Boolean, default=True)
    enable_auto_escalation = Column(Boolean, default=True)
    
    # Business Rules
    trial_duration_days = Column(Integer, default=14)
    max_concurrent_calls = Column(Integer, default=100)
    
    # Last modified
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class BannedProduct(Base):
    """
    Global banned products list - overrides any organisation approval
    """
    __tablename__ = "banned_products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    product_name = Column(String(200), nullable=False, index=True)
    chemical_name = Column(String(200), nullable=True)
    
    ban_reason = Column(Text, nullable=False)
    
    # Compliance
    regulatory_reference = Column(String(255), nullable=True)  # Gov notification number
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit
    banned_by_user_id = Column(Integer, nullable=False)
    banned_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    
    expiry_date = Column(Date, nullable=True)  # For temporary bans
    
    # Additional context data
    extra_data = Column(JSON, nullable=True)
