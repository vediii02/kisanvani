"""
Call Session Service - Production-Ready Implementation
Manages call session lifecycle and state

This service handles:
- Creating new call sessions
- Linking calls to organisations
- Managing call state
- Recording call metadata
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.call_session import CallSession, CallStatus
from db.models.call_state import CallState, StateType
from sqlalchemy import select

logger = logging.getLogger(__name__)


class CallSessionService:
    """
    Service for managing call session lifecycle
    
    Each incoming call creates ONE call session.
    This session tracks everything about the call from start to end.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_call_session(
        self,
        from_phone: str,
        to_phone: str,
        organisation_id: int,
        exotel_call_sid: Optional[str] = None,
        provider_name: str = "exotel"
    ) -> CallSession:
        """
        Create a new call session for incoming call
        
        This is called when:
        - Farmer dials organisation's number
        - Exotel sends webhook to our API
        - System receives incoming call request
        
        Args:
            from_phone: Farmer's phone number (caller ID)
            to_phone: Organisation's phone number (dialed number)
            organisation_id: Identified organisation ID
            exotel_call_sid: Exotel's unique call ID (for telephony tracking)
            provider_name: Telephony provider ('exotel', 'test', 'simulator')
        
        Returns:
            Created CallSession object
            
        Note:
            - session_id: Our internal UUID for tracking
            - exotel_call_sid: Exotel's ID for their system
            - Both IDs are important for call reconciliation
        """
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Create call session record
            call_session = CallSession(
                session_id=session_id,
                phone_number=from_phone,  # Legacy field, stores caller number
                from_phone=from_phone,    # New field: caller's number
                to_phone=to_phone,        # New field: dialed number
                exotel_call_sid=exotel_call_sid,  # Exotel's call ID
                call_direction='inbound',  # Always inbound for farmer calls
                status=CallStatus.ACTIVE,
                provider_name=provider_name,
                provider_call_id=exotel_call_sid,
                start_time=datetime.now(timezone.utc)
            )
            
            # Save to database
            self.db.add(call_session)
            await self.db.commit()
            await self.db.refresh(call_session)
            
            logger.info(
                f"✅ Call session created: ID={call_session.id}, "
                f"Session={session_id[:8]}..., "
                f"From={from_phone}, To={to_phone}, "
                f"Org={organisation_id}"
            )
            
            return call_session
            
        except Exception as e:
            logger.error(f"❌ Error creating call session: {e}")
            await self.db.rollback()
            raise
    
    async def initialize_call_state(
        self,
        call_session_id: int,
        organisation_id: int
    ) -> CallState:
        """
        Initialize call state machine to GREETING state
        
        This sets up the initial state when call starts.
        State machine tracks conversation flow.
        
        Args:
            call_session_id: Call session ID
            organisation_id: Organisation ID
        
        Returns:
            Created CallState object
        """
        try:
            # Create initial state
            call_state = CallState(
                call_session_id=call_session_id,
                state=StateType.GREETING,  # Start with greeting
                state_data={
                    "organisation_id": organisation_id,
                    "stage": "welcome",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                entered_at=datetime.now(timezone.utc)
            )
            
            self.db.add(call_state)
            await self.db.commit()
            await self.db.refresh(call_state)
            
            logger.info(
                f"✅ Call state initialized: "
                f"CallSession={call_session_id}, State=GREETING"
            )
            
            return call_state
            
        except Exception as e:
            logger.error(f"❌ Error initializing call state: {e}")
            await self.db.rollback()
            raise
    
    async def update_call_status(
        self,
        call_session_id: int,
        status: CallStatus,
        end_time: Optional[datetime] = None
    ) -> None:
        """
        Update call session status
        
        Args:
            call_session_id: Call session ID
            status: New status (ACTIVE, COMPLETED, FAILED)
            end_time: End time (optional, defaults to now)
        """
        try:
            call_session = await self.db.get(CallSession, call_session_id)
            if not call_session:
                raise ValueError(f"Call session {call_session_id} not found")
            
            call_session.status = status
            
            if end_time:
                call_session.end_time = end_time
            elif status in [CallStatus.COMPLETED, CallStatus.FAILED]:
                call_session.end_time = datetime.now(timezone.utc)
            
            # Calculate duration if call ended
            if call_session.end_time and call_session.start_time:
                duration = call_session.end_time - call_session.start_time
                call_session.duration_seconds = int(duration.total_seconds())
            
            await self.db.commit()
            
            logger.info(
                f"✅ Call status updated: "
                f"CallSession={call_session_id}, Status={status.value}"
            )
            
        except Exception as e:
            logger.error(f"❌ Error updating call status: {e}")
            await self.db.rollback()
            raise
    
    async def get_call_session(self, call_session_id: int) -> Optional[CallSession]:
        """Get call session by ID"""
        return await self.db.get(CallSession, call_session_id)
    
    async def get_call_metadata(self, call_session_id: int) -> Dict[str, Any]:
        """
        Get comprehensive call metadata
        
        Returns all information about a call session.
        Useful for debugging, analytics, and call review.
        
        Args:
            call_session_id: Call session ID
        
        Returns:
            Dictionary with call metadata
        """
        call_session = await self.get_call_session(call_session_id)
        
        if not call_session:
            return {}
        
        return {
            "call_session_id": call_session.id,
            "session_id": call_session.session_id,
            "from_phone": call_session.from_phone,
            "to_phone": call_session.to_phone,
            "status": call_session.status.value,
            "direction": call_session.call_direction,
            "start_time": call_session.start_time.isoformat() if call_session.start_time else None,
            "end_time": call_session.end_time.isoformat() if call_session.end_time else None,
            "duration_seconds": call_session.duration_seconds,
            "provider": call_session.provider_name,
            "provider_call_id": call_session.provider_call_id,
            "exotel_call_sid": call_session.exotel_call_sid
        }
    
    async def get_or_create_session_by_exotel_sid(
        self,
        exotel_call_sid: str,
        from_phone: str,
        to_phone: str,
        organisation_id: int
    ) -> CallSession:
        """
        Get existing call session by Exotel SID or create new one
        
        This prevents duplicate session creation when Exotel
        sends multiple callbacks for the same call.
        
        Args:
            exotel_call_sid: Exotel's unique call ID
            from_phone: Farmer's phone number
            to_phone: Organisation's phone number
            organisation_id: Organisation ID
        
        Returns:
            Existing or newly created CallSession
        """
        try:
            # Try to find existing session
            result = await self.db.execute(
                select(CallSession).where(
                    CallSession.exotel_call_sid == exotel_call_sid
                )
            )
            call_session = result.scalar_one_or_none()
            
            if call_session:
                logger.info(f"♻️ Found existing call session: {call_session.id}")
                return call_session
            
            # Create new session
            logger.info("🆕 Creating new call session")
            return await self.create_call_session(
                from_phone=from_phone,
                to_phone=to_phone,
                organisation_id=organisation_id,
                exotel_call_sid=exotel_call_sid,
                provider_name="exotel"
            )
            
        except Exception as e:
            logger.error(f"❌ Error in get_or_create_session: {e}")
            raise

