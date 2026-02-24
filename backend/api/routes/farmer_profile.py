"""
Farmer Profile API Routes
Complete farmer management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from api.deps import get_db
from services.farmer_profile_service import farmer_profile_service
from schemas.farmer import FarmerCreate, FarmerUpdate

router = APIRouter()


@router.get("/{farmer_id}")
async def get_farmer(
    farmer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get farmer profile by ID"""
    from db.models.farmer import Farmer
    
    farmer = await db.get(Farmer, farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    return {
        "id": farmer.id,
        "name": farmer.name,
        "phone_number": farmer.phone_number,
        "email": farmer.email,
        "location": farmer.location,
        "district": farmer.district,
        "state": farmer.state,
        "preferred_language": farmer.preferred_language,
        "primary_crop": farmer.primary_crop,
        "land_area_acres": farmer.land_area_acres,
        "soil_type": farmer.soil_type,
        "irrigation_type": farmer.irrigation_type,
        "farming_experience_years": farmer.farming_experience_years,
        "is_active": farmer.is_active,
        "created_at": farmer.created_at.isoformat()
    }


@router.get("/phone/{phone_number}")
async def get_farmer_by_phone(
    phone_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Get or create farmer by phone number"""
    farmer = await farmer_profile_service.get_or_create_farmer(
        phone_number=phone_number,
        db=db,
        auto_create=True
    )
    
    if not farmer:
        raise HTTPException(status_code=500, detail="Failed to get/create farmer")
    
    return {
        "id": farmer.id,
        "phone_number": farmer.phone_number,
        "name": farmer.name,
        "is_new": farmer.name is None
    }


@router.put("/{farmer_id}")
async def update_farmer(
    farmer_id: int,
    update_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update farmer profile"""
    farmer = await farmer_profile_service.update_farmer_profile(
        farmer_id=farmer_id,
        update_data=update_data,
        db=db
    )
    
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    return {
        "success": True,
        "farmer_id": farmer.id,
        "message": "Profile updated successfully"
    }


@router.get("/{farmer_id}/history")
async def get_farmer_history(
    farmer_id: int,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get farmer's interaction history"""
    history = await farmer_profile_service.get_farmer_history(
        farmer_id=farmer_id,
        db=db,
        limit=limit
    )
    
    return history


@router.get("/{farmer_id}/recommendations")
async def get_recommendations(
    farmer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get personalized recommendations for farmer"""
    recommendations = await farmer_profile_service.get_farmer_recommendations(
        farmer_id=farmer_id,
        db=db
    )
    
    return recommendations


@router.get("/search")
async def search_farmers(
    location: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    primary_crop: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search farmers with filters"""
    filters = {}
    if location:
        filters["location"] = location
    if district:
        filters["district"] = district
    if primary_crop:
        filters["primary_crop"] = primary_crop
    if language:
        filters["language"] = language
    
    result = await farmer_profile_service.search_farmers(
        db=db,
        filters=filters if filters else None,
        page=page,
        page_size=page_size
    )
    
    return result
