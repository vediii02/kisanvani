"""
API Routes for Organisation Phone Number Management

These endpoints handle phone number CRUD operations for multi-tenant routing.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from db.session import get_db
from services.phone_number_service import phone_number_service
from db.models.organisation_phone import OrganisationPhoneNumber
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/org-phone-numbers", tags=["Organisation Phone Numbers"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class PhoneNumberCreate(BaseModel):
    """Schema for creating a new phone number"""
    organisation_id: int = Field(..., description="Organisation ID that will own this number")
    phone_number: str = Field(..., description="Phone number in any format (will be normalized)")
    channel: str = Field(default="voice", description="Channel type: voice, whatsapp, sms")
    region: Optional[str] = Field(None, description="Geographic area/region this number serves")
    display_name: Optional[str] = Field(None, description="Friendly name for this number")
    is_active: bool = Field(default=True, description="Active status")

class PhoneNumberUpdate(BaseModel):
    """Schema for updating a phone number"""
    phone_number: Optional[str] = Field(None, description="New phone number (Super Admin only)")
    is_active: Optional[bool] = Field(None, description="Active status")
    region: Optional[str] = Field(None, description="Geographic area/region")
    display_name: Optional[str] = Field(None, description="Friendly name")

class PhoneNumberResponse(BaseModel):
    """Schema for phone number response"""
    id: int
    organisation_id: int
    phone_number: str
    channel: str
    is_active: bool
    region: Optional[str]
    display_name: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/", response_model=PhoneNumberResponse)
async def add_phone_number(
    phone_data: PhoneNumberCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Add a new phone number to an organisation.
    
    **Super Admin Use Case:**
    When creating a new organisation, Super Admin must add at least one phone number.
    
    **Business Rules:**
    - Phone number must be unique across the entire platform
    - Phone number will be normalized automatically
    - Organisation must exist and be active
    
    **Example:**
    ```json
    {
      "organisation_id": 1,
      "phone_number": "+91 9999888877",
      "display_name": "Main Helpline",
      "region": "All India",
      "is_active": true
    }
    ```
    """
    phone_record, error = await phone_number_service.add_phone_number(
        db=db,
        organisation_id=phone_data.organisation_id,
        phone_number=phone_data.phone_number,
        channel=phone_data.channel,
        region=phone_data.region,
        display_name=phone_data.display_name,
        is_active=phone_data.is_active
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return phone_record


@router.get("/organisation/{organisation_id}", response_model=List[PhoneNumberResponse])
async def get_organisation_phone_numbers(
    organisation_id: int,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all phone numbers for an organisation.
    
    **Organisation Admin Use Case:**
    Display all phone numbers assigned to their organisation on the dashboard.
    
    **Super Admin Use Case:**
    View all phone numbers for any organisation during management.
    
    **Query Parameters:**
    - active_only: If true, return only active numbers
    """
    phone_numbers = await phone_number_service.get_organisation_phone_numbers(
        db=db,
        organisation_id=organisation_id,
        active_only=active_only
    )
    
    return phone_numbers


@router.put("/{phone_id}", response_model=PhoneNumberResponse)
async def update_phone_number(
    phone_id: int,
    phone_data: PhoneNumberUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a phone number record.
    
    **Organisation Admin Can Update:**
    - is_active: Toggle number on/off
    - region: Update geographic area
    - display_name: Update friendly name
    
    **Super Admin Can Also Update:**
    - phone_number: Change the actual phone number
    
    **Use Cases:**
    1. Temporarily disable a number: Set is_active = false
    2. Update region assignment: Set region = "Maharashtra"
    3. Update display name: Set display_name = "Punjab Regional Office"
    4. Change phone number: Set phone_number = "+919999888877" (Super Admin only)
    """
    phone_record, error = await phone_number_service.update_phone_number(
        db=db,
        phone_id=phone_id,
        phone_number=phone_data.phone_number,
        is_active=phone_data.is_active,
        region=phone_data.region,
        display_name=phone_data.display_name
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return phone_record


@router.delete("/{phone_id}")
async def delete_phone_number(
    phone_id: int,
    force: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a phone number.
    
    **Safety Check:**
    By default, prevents deletion of the last active phone number for an organisation.
    Use force=true to override (Super Admin only).
    
    **Business Rule:**
    An organisation MUST have at least one active phone number to receive calls.
    
    **Query Parameters:**
    - force: Override safety check (default: false)
    """
    success, error = await phone_number_service.delete_phone_number(
        db=db,
        phone_id=phone_id,
        force=force
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"success": True, "message": "Phone number deleted successfully"}


@router.get("/lookup/{phone_number}")
async def lookup_phone_number(
    phone_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Lookup which organisation owns a phone number.
    
    **Primary Use Case: CALL ROUTING**
    This endpoint is used internally to route incoming calls to the correct organisation.
    
    **Example Flow:**
    1. Farmer calls 9999888877
    2. System calls this endpoint: /lookup/9999888877
    3. Returns organisation_id and details
    4. System loads organisation-specific AI config
    5. AI responds with organisation-specific greeting
    
    **Response:**
    ```json
    {
      "organisation_id": 1,
      "organisation_name": "Ankur Seeds",
      "phone_record": {
        "id": 1,
        "phone_number": "9999888877",
        "region": "All India",
        "display_name": "Main Helpline"
      }
    }
    ```
    """
    org_id, phone_record, error = await phone_number_service.find_organisation_by_phone(
        db=db,
        phone_number=phone_number,
        require_active=True
    )
    
    if error:
        raise HTTPException(status_code=404, detail=error)
    
    # Also fetch organisation details
    from db.models.organisation import Organisation
    from sqlalchemy import select
    
    org_result = await db.execute(
        select(Organisation).where(Organisation.id == org_id)
    )
    org = org_result.scalar_one()
    
    return {
        "organisation_id": org_id,
        "organisation_name": org.name,
        "organisation_status": org.status,
        "phone_record": {
            "id": phone_record.id,
            "phone_number": phone_record.phone_number,
            "region": phone_record.region,
            "display_name": phone_record.display_name,
            "is_active": phone_record.is_active
        }
    }
