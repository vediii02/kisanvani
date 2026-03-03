from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from datetime import datetime, timezone
from db.base import Base
import enum

class FarmerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class Farmer(Base):
    __tablename__ = "farmers"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(15), index=True, nullable=False)
    name = Column(String(200))
    village = Column(String(200))
    district = Column(String(200))
    state = Column(String(200))
    crop_type = Column(String(200))
    land_size = Column(String(50))
    crop_area = Column(String(100))
    problem_area = Column(String(200))
    crop_age_days = Column(String(200))
    language = Column(String(10), default='hi')
    status = Column(SQLEnum(FarmerStatus), default=FarmerStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))