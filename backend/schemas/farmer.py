from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class FarmerBase(BaseModel):
    phone_number: str
    name: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    crop_type: Optional[str] = None
    land_size: Optional[str] = None
    crop_area: Optional[str] = None
    problem_area: Optional[str] = None
    language: str = 'hi'

class FarmerCreate(FarmerBase):
    pass

class FarmerUpdate(BaseModel):
    name: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    crop_type: Optional[str] = None
    land_size: Optional[str] = None
    crop_area: Optional[str] = None
    problem_area: Optional[str] = None
    language: Optional[str] = None

class FarmerResponse(FarmerBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True