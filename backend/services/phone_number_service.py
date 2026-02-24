"""
Organisation Phone Number Management Service

This service handles all phone number operations for multi-tenant call routing.
Critical for SaaS model where each organisation gets unique phone numbers.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from db.models.organisation_phone import OrganisationPhoneNumber
from db.models.organisation import Organisation
from typing import Optional, List
import re
import logging

logger = logging.getLogger(__name__)


class PhoneNumberService:
    """
    Service layer for managing organisation phone numbers.
    
    Business Rules Enforced:
    1. Phone number uniqueness across entire platform
    2. One organisation can have multiple numbers
    3. One number can belong to only one organisation
    4. Phone number format validation
    5. Active/inactive status management
    """
    
    def __init__(self):
        self.phone_regex = re.compile(r'^[\d+\-\(\)\s]+$')  # Allow digits, +, -, (), spaces
    
    def normalize_phone_number(self, phone: str) -> str:
        """
        Normalize phone number to consistent format.
        Removes spaces, dashes, parentheses.
        
        Examples:
        - "+91 98765 43210" -> "+919876543210"
        - "9999888877" -> "9999888877"
        - "+91-9876543210" -> "+919876543210"
        """
        # Remove all non-digit characters except leading +
        normalized = re.sub(r'[^\d+]', '', phone)
        return normalized
    
    def validate_phone_number(self, phone: str) -> tuple[bool, Optional[str]]:
        """
        Validate phone number format.
        
        Returns: (is_valid, error_message)
        """
        if not phone or len(phone.strip()) == 0:
            return False, "Phone number cannot be empty"
        
        normalized = self.normalize_phone_number(phone)
        
        # Must have at least 10 digits
        digits_only = re.sub(r'\D', '', normalized)
        if len(digits_only) < 10:
            return False, "Phone number must have at least 10 digits"
        
        if len(digits_only) > 15:
            return False, "Phone number too long (max 15 digits)"
        
        return True, None
    
    async def check_phone_availability(
        self,
        db: AsyncSession,
        phone_number: str,
        exclude_id: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if phone number is available (not already assigned to another org).
        
        Args:
            phone_number: The phone number to check
            exclude_id: Optional phone number record ID to exclude (for updates)
        
        Returns: (is_available, error_message)
        """
        normalized = self.normalize_phone_number(phone_number)
        
        query = select(OrganisationPhoneNumber).where(
            OrganisationPhoneNumber.phone_number == normalized
        )
        
        if exclude_id:
            query = query.where(OrganisationPhoneNumber.id != exclude_id)
        
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            return False, f"Phone number already assigned to organisation ID {existing.organisation_id}"
        
        return True, None
    
    async def add_phone_number(
        self,
        db: AsyncSession,
        organisation_id: int,
        phone_number: str,
        channel: str = "voice",
        region: Optional[str] = None,
        display_name: Optional[str] = None,
        is_active: bool = True
    ) -> tuple[Optional[OrganisationPhoneNumber], Optional[str]]:
        """
        Add a new phone number to an organisation.
        
        This is the primary method for phone number provisioning.
        Super Admin uses this when creating/updating organisations.
        
        Returns: (phone_number_record, error_message)
        """
        # Validate phone number format
        is_valid, error = self.validate_phone_number(phone_number)
        if not is_valid:
            return None, error
        
        # Normalize before storing
        normalized = self.normalize_phone_number(phone_number)
        
        # Check if phone already exists
        is_available, error = await self.check_phone_availability(db, normalized)
        if not is_available:
            return None, error
        
        # Verify organisation exists
        org_result = await db.execute(
            select(Organisation).where(Organisation.id == organisation_id)
        )
        org = org_result.scalar_one_or_none()
        if not org:
            return None, f"Organisation with ID {organisation_id} not found"
        
        # Create new phone number record
        phone_record = OrganisationPhoneNumber(
            organisation_id=organisation_id,
            phone_number=normalized,
            channel=channel,
            is_active=is_active,
            region=region,
            display_name=display_name
        )
        
        db.add(phone_record)
        await db.commit()
        await db.refresh(phone_record)
        
        logger.info(
            f"Added phone number {normalized} to organisation {organisation_id} "
            f"(display_name: {display_name}, region: {region})"
        )
        
        return phone_record, None
    
    async def update_phone_number(
        self,
        db: AsyncSession,
        phone_id: int,
        phone_number: Optional[str] = None,
        is_active: Optional[bool] = None,
        region: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> tuple[Optional[OrganisationPhoneNumber], Optional[str]]:
        """
        Update an existing phone number record.
        
        Organisation admins can update status, region, display_name.
        Only Super Admin can change the actual phone_number field.
        """
        # Fetch existing record
        result = await db.execute(
            select(OrganisationPhoneNumber).where(OrganisationPhoneNumber.id == phone_id)
        )
        phone_record = result.scalar_one_or_none()
        
        if not phone_record:
            return None, f"Phone number record {phone_id} not found"
        
        # Update phone number if provided
        if phone_number:
            is_valid, error = self.validate_phone_number(phone_number)
            if not is_valid:
                return None, error
            
            normalized = self.normalize_phone_number(phone_number)
            
            # Check availability (excluding current record)
            is_available, error = await self.check_phone_availability(db, normalized, exclude_id=phone_id)
            if not is_available:
                return None, error
            
            phone_record.phone_number = normalized
        
        # Update other fields
        if is_active is not None:
            phone_record.is_active = is_active
        
        if region is not None:
            phone_record.region = region
        
        if display_name is not None:
            phone_record.display_name = display_name
        
        await db.commit()
        await db.refresh(phone_record)
        
        logger.info(f"Updated phone number record {phone_id}")
        
        return phone_record, None
    
    async def delete_phone_number(
        self,
        db: AsyncSession,
        phone_id: int,
        force: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Delete a phone number.
        
        Args:
            phone_id: ID of phone number to delete
            force: If False, check if it's the last active number (safety check)
        
        Returns: (success, error_message)
        """
        # Fetch phone number
        result = await db.execute(
            select(OrganisationPhoneNumber).where(OrganisationPhoneNumber.id == phone_id)
        )
        phone_record = result.scalar_one_or_none()
        
        if not phone_record:
            return False, f"Phone number record {phone_id} not found"
        
        # Safety check: Don't delete if it's the last active number (unless forced)
        if not force:
            active_count_result = await db.execute(
                select(OrganisationPhoneNumber).where(
                    and_(
                        OrganisationPhoneNumber.organisation_id == phone_record.organisation_id,
                        OrganisationPhoneNumber.is_active == True,
                        OrganisationPhoneNumber.id != phone_id
                    )
                )
            )
            other_active_numbers = active_count_result.scalars().all()
            
            if len(other_active_numbers) == 0:
                return False, "Cannot delete the last active phone number. Organisation must have at least one active number."
        
        await db.delete(phone_record)
        await db.commit()
        
        logger.info(f"Deleted phone number {phone_record.phone_number} (ID: {phone_id})")
        
        return True, None
    
    async def get_organisation_phone_numbers(
        self,
        db: AsyncSession,
        organisation_id: int,
        active_only: bool = False
    ) -> List[OrganisationPhoneNumber]:
        """
        Get all phone numbers for an organisation.
        
        Used by:
        - Organisation Dashboard to display assigned numbers
        - Super Admin to view org phone numbers
        """
        query = select(OrganisationPhoneNumber).where(
            OrganisationPhoneNumber.organisation_id == organisation_id
        )
        
        if active_only:
            query = query.where(OrganisationPhoneNumber.is_active == True)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def find_organisation_by_phone(
        self,
        db: AsyncSession,
        phone_number: str,
        require_active: bool = True
    ) -> tuple[Optional[int], Optional[OrganisationPhoneNumber], Optional[str]]:
        """
        **CRITICAL METHOD FOR CALL ROUTING**
        
        Find which organisation owns a phone number.
        This is called for EVERY incoming call to route it correctly.
        
        Args:
            phone_number: The 'to_phone' from incoming call
            require_active: If True, only return active phone numbers
        
        Returns: (organisation_id, phone_record, error_message)
        
        Usage in call flow:
            org_id, phone_record, error = await phone_service.find_organisation_by_phone(
                db, to_phone="+919999888877"
            )
            if not org_id:
                # Reject call with polite message
                return {"error": error}
            
            # Load organisation-specific AI config
            org = await get_organisation(db, org_id)
            greeting = org.greeting_message or f"Namaste, aap {org.name} se baat kar rahe hain"
        """
        normalized = self.normalize_phone_number(phone_number)
        
        query = select(OrganisationPhoneNumber).where(
            OrganisationPhoneNumber.phone_number == normalized
        )
        
        if require_active:
            query = query.where(OrganisationPhoneNumber.is_active == True)
        
        result = await db.execute(query)
        phone_record = result.scalar_one_or_none()
        
        if not phone_record:
            return None, None, f"No active organisation found for phone number {phone_number}"
        
        # Also verify the organisation itself is active
        org_result = await db.execute(
            select(Organisation).where(Organisation.id == phone_record.organisation_id)
        )
        org = org_result.scalar_one_or_none()
        
        if not org:
            return None, None, f"Organisation not found for phone number {phone_number}"
        
        if org.status != "active":
            return None, None, f"Organisation for phone number {phone_number} is not active"
        
        logger.info(
            f"Call routing: Phone {phone_number} -> Organisation {org.name} (ID: {org.id})"
        )
        
        return phone_record.organisation_id, phone_record, None


# Singleton instance
phone_number_service = PhoneNumberService()
