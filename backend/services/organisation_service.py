"""
Organisation Service - Production-Ready Implementation
Handles organisation identification and configuration for multi-tenant AI system

This service is the CORE of multi-tenancy:
- Each organisation has its own phone numbers
- AI behavior is customized per organisation
- Farmers are automatically routed based on dialed number
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models.organisation import Organisation
from db.models.organisation_phone import OrganisationPhoneNumber

logger = logging.getLogger(__name__)


class OrganisationService:
    """
    Service for organisation-specific operations in multi-tenant system
    
    Key Principle: NEVER ask farmer which organisation they're calling.
    Organisation is identified ONLY by the phone number they dialed (to_phone).
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def identify_organisation_by_phone(
        self, 
        dialed_number: str
    ) -> Optional[Organisation]:
        """
        Identify organisation by the phone number farmer dialed
        
        This is the ENTRY POINT for all incoming calls.
        The dialed number (to_phone) is the ONLY way to know which organisation
        the farmer is trying to reach.
        
        Args:
            dialed_number: The phone number farmer dialed (to_phone from Exotel)
        
        Returns:
            Organisation object if found, None otherwise
            
        Example:
            Farmer dials: 9999888877
            System checks: organisation_phone_numbers.phone_number = '9999888877'
            Finds: organisation_id = 2 (Rasi Seeds)
            Returns: Organisation(id=2, name='Rasi Seeds', ...)
        """
        try:
            # Step 1: Find phone number record
            # This tells us which organisation owns this number
            result = await self.db.execute(
                select(OrganisationPhoneNumber)
                .where(
                    OrganisationPhoneNumber.phone_number == dialed_number,
                    OrganisationPhoneNumber.is_active == True  # Only active numbers
                )
            )
            org_phone = result.scalar_one_or_none()
            
            if not org_phone:
                logger.warning(f"❌ No active organisation found for phone: {dialed_number}")
                return None
            
            # Step 2: Load organisation details
            organisation = await self.db.get(Organisation, org_phone.organisation_id)
            
            if not organisation:
                logger.error(
                    f"❌ Data inconsistency: Phone record exists but organisation "
                    f"not found (org_id={org_phone.organisation_id})"
                )
                return None
            
            logger.info(
                f"✅ Organisation identified: {organisation.name} "
                f"(ID: {organisation.id}) for phone {dialed_number}"
            )
            
            return organisation
            
        except Exception as e:
            logger.error(f"❌ Error identifying organisation: {e}")
            raise
    
    def get_organisation_greeting(
        self, 
        organisation: Organisation,
        farmer_name: Optional[str] = None
    ) -> str:
        """
        Generate generic greeting message (without organisation name)
        
        Simple greeting for all farmers without mentioning organisation.
        Organisation is identified internally but not spoken to farmer.
        
        Args:
            organisation: Organisation object (used for internal tracking only)
            farmer_name: Farmer's name if known (optional)
        
        Returns:
            Hindi greeting text WITHOUT organisation name
            
        Example Output:
            "Namaste! Main Kisan AI hun, aapki kheti sahayak."
            "Main aapki kheti se judi samasya mein madad kar sakti hun."
        """
        # Base greeting without organisation name
        greeting = """नमस्ते! मैं किसान AI हूं, आपकी खेती सहायक।

मैं आपकी खेती से जुड़ी समस्या में मदद कर सकती हूं।"""
        
        # Personalize if farmer name is known
        if farmer_name:
            greeting = f"""नमस्ते {farmer_name} जी! मैं किसान AI हूं, आपकी खेती सहायक।

मैं आपकी खेती से जुड़ी समस्या में मदद कर सकती हूं।"""
        
        return greeting.strip()
    
    async def get_organisation_config(
        self, 
        organisation_id: int
    ) -> Dict[str, Any]:
        """
        Get organisation-specific configuration
        
        In future, each organisation may have:
        - Custom products/services
        - Regional language preferences
        - Specific escalation contacts
        - Custom voice settings
        
        Args:
            organisation_id: Organisation ID
        
        Returns:
            Configuration dictionary
        """
        organisation = await self.db.get(Organisation, organisation_id)
        
        if not organisation:
            return {}
        
        # Default configuration
        # In future, this can be stored in database or config files
        config = {
            "organisation_id": organisation.id,
            "organisation_name": organisation.name,
            "language": "hi",  # Hindi
            "voice_gender": "FEMALE",
            "products_enabled": True,
            "advisory_enabled": True,
            "escalation_enabled": True,
            # Future: Load from organisation settings table
        }
        
        return config
    
    async def validate_phone_ownership(
        self,
        phone_number: str,
        organisation_id: int
    ) -> bool:
        """
        Verify that a phone number belongs to specified organisation
        
        Used for security checks and validation.
        
        Args:
            phone_number: Phone number to check
            organisation_id: Organisation ID to validate against
        
        Returns:
            True if phone belongs to organisation, False otherwise
        """
        result = await self.db.execute(
            select(OrganisationPhoneNumber)
            .where(
                OrganisationPhoneNumber.phone_number == phone_number,
                OrganisationPhoneNumber.organisation_id == organisation_id,
                OrganisationPhoneNumber.is_active == True
            )
        )
        
        return result.scalar_one_or_none() is not None
    
    async def get_organisation_phone_numbers(
        self,
        organisation_id: int
    ) -> list[OrganisationPhoneNumber]:
        """
        Get all phone numbers for an organisation
        
        Args:
            organisation_id: Organisation ID
        
        Returns:
            List of phone number records
        """
        result = await self.db.execute(
            select(OrganisationPhoneNumber)
            .where(
                OrganisationPhoneNumber.organisation_id == organisation_id,
                OrganisationPhoneNumber.is_active == True
            )
        )
        
        return result.scalars().all()


# Singleton instance for easy import
# Usage: from services.organisation_service import organisation_service
# org = await organisation_service.identify_organisation_by_phone(db, phone)
