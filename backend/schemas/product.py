# schemas/product.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    name: str
    category: str
    sub_category: Optional[str] = None
    description: Optional[str] = None
    target_crops: Optional[str] = None
    target_problems: Optional[str] = None
    dosage: Optional[str] = None
    usage_instructions: Optional[str] = None
    safety_precautions: Optional[str] = None
    price_range: Optional[str] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    organisation_id: int
    company_id: int
    brand_id: int


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None
    target_crops: Optional[str] = None
    target_problems: Optional[str] = None
    dosage: Optional[str] = None
    usage_instructions: Optional[str] = None
    safety_precautions: Optional[str] = None
    price_range: Optional[str] = None
    is_active: Optional[bool] = None
    company_id: Optional[int] = None
    brand_id: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    organisation_id: int
    company_id: Optional[int] = None
    brand_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
