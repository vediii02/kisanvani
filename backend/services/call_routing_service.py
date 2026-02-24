"""
Call Routing Service - Multi-Tenant Call Handling

This is the CORE of the multi-tenant system.
Routes incoming calls based on dialed phone number (to_phone).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.call_session import CallSession, CallStatus
from db.models.organisation import Organisation
from db.models.farmer import Farmer
from services.phone_number_service import phone_number_service
from typing import Optional, Dict, Any
import logging
import secrets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CallRoutingService:
    """
    Handles incoming call routing for multi-tenant system.
    
    Key Responsibilities:
    1. Identify organisation from dialed phone number
    2. Create/update farmer record
    3. Initialize call session
    4. Load organisation-specific configuration
    5. Generate organisation-specific greeting
    """
    
    async def handle_incoming_call(
        self,
        db: AsyncSession,
        from_phone: str,
        to_phone: str,
        call_metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[Optional[CallSession], Optional[Organisation], Optional[str]]:
        """
        Handle an incoming call and route it to the correct organisation.
        
        This method is called for EVERY incoming call (simulator or real Exotel).
        
        **Critical Flow:**
        1. Use to_phone to identify organisation (NEVER ask farmer)
        2. Verify organisation is active
        3. Get/create farmer record
        4. Create call session with organisation context
        5. Return call session ready for AI interaction
        
        Args:
            from_phone: Caller's phone number (farmer)
            to_phone: Dialed number (organisation's phone)
            call_metadata: Optional metadata (call_id, source, etc.)
        
        Returns:
            (call_session, organisation, error_message)
        
        Error Cases:
        - Phone number not found: "Sorry, this number is not in service"
        - Organisation inactive: "Service temporarily unavailable"
        - System error: "Technical issue, please try again"
        """
        logger.info(f"Incoming call: from={from_phone}, to={to_phone}")
        
        # STEP 1: Identify organisation from to_phone (primary_phone lookup)
        # Look up organisation by primary_phone field directly
        org_result = await db.execute(
            select(Organisation).where(
                Organisation.primary_phone == to_phone,
                Organisation.status == "active"
            )
        )
        organisation = org_result.scalar_one_or_none()
        
        if not organisation:
            logger.warning(f"Call rejected: Phone number {to_phone} not found or organisation inactive")
            return None, None, "यह नंबर सेवा में नहीं है। कृपया सही नंबर डायल करें।"
        
        # STEP 2: Get or create farmer record
        farmer = await self._get_or_create_farmer(db, from_phone, organisation.id)
        
        # STEP 3: Create call session
        # Note: Using existing CallSession fields, organisation_id stored in farmer record
        session_id = f"sim_{int(datetime.now().timestamp())}_{secrets.token_hex(4)}"
        
        # Get source from metadata
        source = call_metadata.get('source', 'unknown') if call_metadata else 'unknown'
        provider = "simulator" if source == "simulator" else "exotel"
        
        call_session = CallSession(
            session_id=session_id,
            farmer_id=farmer.id,
            phone_number=from_phone,
            from_phone=from_phone,
            to_phone=to_phone,  # Store which number was dialed
            status=CallStatus.ACTIVE,
            provider_name=provider
        )
        
        db.add(call_session)
        await db.commit()
        await db.refresh(call_session)
        
        logger.info(
            f"✅ Call session created: ID={call_session.id}, "
            f"Farmer={farmer.id}, Org={organisation.name} (ID={organisation.id}), "
            f"Provider={call_session.provider_name}"
        )
        
        return call_session, organisation, None
    
    async def _get_or_create_farmer(
        self,
        db: AsyncSession,
        phone_number: str,
        organisation_id: int
    ) -> Farmer:
        """
        Get existing farmer or create new one.
        
        Note: Farmers can call multiple organisations,
        but each farmer record is tied to the first org they called.
        """
        # Normalize phone number
        normalized_phone = phone_number_service.normalize_phone_number(phone_number)
        
        # Try to find existing farmer
        result = await db.execute(
            select(Farmer).where(Farmer.phone_number == normalized_phone)
        )
        farmer = result.scalar_one_or_none()
        
        if farmer:
            logger.info(f"Existing farmer found: ID={farmer.id}, Phone={normalized_phone}")
            return farmer
        
        # Create new farmer
        farmer = Farmer(
            phone_number=normalized_phone,
            language='hi',  # Default to Hindi
            status='active'
        )
        
        db.add(farmer)
        await db.commit()
        await db.refresh(farmer)
        
        logger.info(f"New farmer created: ID={farmer.id}, Phone={normalized_phone}")
        
        return farmer
    
    async def get_organisation_greeting(
        self,
        db: AsyncSession,
        organisation_id: int,
        language: str = 'hi'
    ) -> str:
        """
        Get organisation-specific greeting message.
        
        This is what the AI says first when a farmer calls.
        
        **Examples:**
        - "Namaste, aap Ankur Seeds Kisan Sahayak AI se baat kar rahe hain"
        - "Hello, you are speaking with Rasi Seeds Farmer Support AI"
        - "नमस्ते, आप Mahindra Agri Kisan Sahayak से बात कर रहे हैं"
        
        **Customization:**
        1. If org has custom greeting_message, use that
        2. Otherwise, use default template with org name
        3. Future: Support multiple languages
        """
        result = await db.execute(
            select(Organisation).where(Organisation.id == organisation_id)
        )
        org = result.scalar_one_or_none()
        
        if not org:
            return "नमस्ते, किसान सहायक AI में आपका स्वागत है"
        
        # Use custom greeting if available
        if org.greeting_message:
            return org.greeting_message
        
        # Default greeting template
        if language == 'hi':
            return f"नमस्ते, आप {org.name} किसान सहायक AI से बात कर रहे हैं। मैं आपकी कैसे मदद कर सकता हूं?"
        elif language == 'en':
            return f"Hello, you are speaking with {org.name} Farmer Support AI. How can I help you?"
        else:
            return f"Namaste, aap {org.name} Kisan Sahayak AI se baat kar rahe hain. Main aapki kaise madad kar sakta hun?"
    
    async def get_call_context(
        self,
        db: AsyncSession,
        call_session_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get complete context for a call session.
        
        Used by AI to make organisation-specific decisions:
        - Which products to recommend (only approved for this org)
        - Which knowledge base to query
        - Which language to use
        - Escalation contacts
        
        Returns:
            {
                "call_session": {...},
                "organisation": {...},
                "farmer": {...},
                "phone_record": {...}
            }
        """
        # Fetch call session with relationships
        call_result = await db.execute(
            select(CallSession).where(CallSession.id == call_session_id)
        )
        call_session = call_result.scalar_one_or_none()
        
        if not call_session:
            return None
        
        # Fetch organisation
        org_result = await db.execute(
            select(Organisation).where(Organisation.id == call_session.organisation_id)
        )
        organisation = org_result.scalar_one_or_none()
        
        # Fetch farmer
        farmer_result = await db.execute(
            select(Farmer).where(Farmer.id == call_session.farmer_id)
        )
        farmer = farmer_result.scalar_one_or_none()
        
        # Fetch phone record
        org_id, phone_record, _ = await phone_number_service.find_organisation_by_phone(
            db=db,
            phone_number=call_session.dialed_number,
            require_active=False  # Get record even if inactive
        )
        
        return {
            "call_session": {
                "id": call_session.id,
                "status": call_session.status,
                "language": call_session.language,
                "created_at": call_session.created_at.isoformat() if call_session.created_at else None
            },
            "organisation": {
                "id": organisation.id if organisation else None,
                "name": organisation.name if organisation else None,
                "preferred_languages": organisation.preferred_languages if organisation else "hi",
                "greeting_message": organisation.greeting_message if organisation else None
            } if organisation else None,
            "farmer": {
                "id": farmer.id if farmer else None,
                "phone_number": farmer.phone_number if farmer else None,
                "name": farmer.name if farmer else None,
                "language": farmer.language if farmer else None
            } if farmer else None,
            "phone_record": {
                "phone_number": phone_record.phone_number if phone_record else None,
                "region": phone_record.region if phone_record else None,
                "display_name": phone_record.display_name if phone_record else None
            } if phone_record else None
        }


# Singleton instance
call_routing_service = CallRoutingService()
