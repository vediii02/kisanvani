"""State machine for call flow management"""

from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models.call_session import CallSession
from db.models.call_state import CallState, StateType


class StateMachine:
    """
    Manages call flow state transitions
    
    State Flow:
    INCOMING → GREETING → PROFILING → PROBLEM → (ADVISORY | ESCALATED) → CLOSURE → ENDED
    """
    
    # Define valid state transitions
    TRANSITIONS = {
        StateType.INCOMING: [StateType.GREETING, StateType.ENDED],
        StateType.GREETING: [StateType.PROFILING, StateType.ENDED],
        StateType.PROFILING: [StateType.PROBLEM, StateType.ENDED],
        StateType.PROBLEM: [StateType.ADVISORY, StateType.ESCALATED, StateType.ENDED],
        StateType.ADVISORY: [StateType.CLOSURE, StateType.ESCALATED, StateType.ENDED],
        StateType.ESCALATED: [StateType.CLOSURE, StateType.ENDED],
        StateType.CLOSURE: [StateType.ENDED],
        StateType.ENDED: []  # Terminal state
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_current_state(self, call_session_id: int) -> Optional[CallState]:
        """Get the current active state for a call"""
        result = await self.db.execute(
            select(CallState)
            .where(
                CallState.call_session_id == call_session_id,
                CallState.exited_at.is_(None)
            )
            .order_by(CallState.entered_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_state_history(self, call_session_id: int) -> List[CallState]:
        """Get all states for a call in chronological order"""
        result = await self.db.execute(
            select(CallState)
            .where(CallState.call_session_id == call_session_id)
            .order_by(CallState.entered_at)
        )
        return list(result.scalars().all())
    
    async def transition_to(
        self,
        call_session_id: int,
        new_state: StateType,
        state_data: Optional[Dict] = None
    ) -> CallState:
        """
        Transition to a new state
        
        Args:
            call_session_id: ID of the call session
            new_state: Target state to transition to
            state_data: Optional data to store with the state
            
        Returns:
            The new CallState object
            
        Raises:
            ValueError: If transition is invalid
        """
        # Get current state
        current_state = await self.get_current_state(call_session_id)
        
        # Validate transition
        if current_state:
            current_state_type = current_state.state
            valid_transitions = self.TRANSITIONS.get(current_state_type, [])
            
            if new_state not in valid_transitions:
                raise ValueError(
                    f"Invalid transition from {current_state_type.value} to {new_state.value}. "
                    f"Valid transitions: {[s.value for s in valid_transitions]}"
                )
            
            # Close current state
            current_state.exited_at = datetime.utcnow()
            await self.db.commit()
        
        # Create new state
        new_state_obj = CallState(
            call_session_id=call_session_id,
            state=new_state,
            entered_at=datetime.utcnow(),
            state_data=state_data or {}
        )
        
        self.db.add(new_state_obj)
        await self.db.commit()
        await self.db.refresh(new_state_obj)
        
        return new_state_obj
    
    async def is_state_active(self, call_session_id: int, state: StateType) -> bool:
        """Check if a specific state is currently active"""
        current_state = await self.get_current_state(call_session_id)
        return current_state and current_state.state == state
    
    async def get_time_in_state(self, call_state: CallState) -> float:
        """Get time spent in a state (in seconds)"""
        if call_state.exited_at:
            return (call_state.exited_at - call_state.entered_at).total_seconds()
        else:
            return (datetime.utcnow() - call_state.entered_at).total_seconds()
    
    async def force_end_call(self, call_session_id: int, reason: str = None):
        """Force end a call from any state"""
        current_state = await self.get_current_state(call_session_id)
        
        if current_state and current_state.state != StateType.ENDED:
            await self.transition_to(
                call_session_id,
                StateType.ENDED,
                state_data={"forced": True, "reason": reason}
            )
    
    async def get_state_duration_summary(self, call_session_id: int) -> Dict[str, float]:
        """Get time spent in each state for analytics"""
        states = await self.get_state_history(call_session_id)
        
        summary = {}
        for state in states:
            state_name = state.state.value
            duration = await self.get_time_in_state(state)
            summary[state_name] = duration
        
        return summary


class CallFlowManager:
    """
    High-level manager for call flow operations
    Orchestrates state machine with business logic
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_machine = StateMachine(db)
    
    async def start_call(self, call_session_id: int, from_phone: str, to_phone: str):
        """Initialize a new call flow"""
        # Transition to INCOMING state
        await self.state_machine.transition_to(
            call_session_id,
            StateType.INCOMING,
            state_data={
                "from_phone": from_phone,
                "to_phone": to_phone,
                "started_at": datetime.utcnow().isoformat()
            }
        )
    
    async def handle_greeting_response(
        self,
        call_session_id: int,
        consent_given: bool,
        farmer_name: Optional[str] = None
    ):
        """Handle farmer's response to greeting"""
        if consent_given:
            await self.state_machine.transition_to(
                call_session_id,
                StateType.PROFILING,
                state_data={
                    "consent_given": True,
                    "farmer_name": farmer_name,
                    "questions_completed": 0
                }
            )
        else:
            await self.state_machine.transition_to(
                call_session_id,
                StateType.ENDED,
                state_data={
                    "consent_given": False,
                    "reason": "consent_declined"
                }
            )
    
    async def update_profiling_progress(
        self,
        call_session_id: int,
        questions_completed: int,
        total_questions: int
    ):
        """Update profiling progress"""
        current_state = await self.state_machine.get_current_state(call_session_id)
        
        if current_state and current_state.state == StateType.PROFILING:
            current_state.state_data.update({
                "questions_completed": questions_completed,
                "total_questions": total_questions,
                "progress_percent": (questions_completed / total_questions) * 100
            })
            await self.db.commit()
    
    async def complete_profiling(self, call_session_id: int):
        """Profiling completed, move to problem understanding"""
        await self.state_machine.transition_to(
            call_session_id,
            StateType.PROBLEM,
            state_data={
                "profiling_completed": True,
                "waiting_for_problem_description": True
            }
        )
    
    async def process_problem_description(
        self,
        call_session_id: int,
        symptoms_detected: List[str],
        confidence: float
    ):
        """Problem described, decide on advisory or escalation"""
        # Update current state with detected symptoms
        current_state = await self.state_machine.get_current_state(call_session_id)
        if current_state:
            current_state.state_data.update({
                "symptoms_detected": symptoms_detected,
                "symptom_confidence": confidence,
                "symptom_count": len(symptoms_detected)
            })
            await self.db.commit()
    
    async def provide_advisory(
        self,
        call_session_id: int,
        advisory_id: int,
        confidence: float
    ):
        """Transition to advisory state"""
        await self.state_machine.transition_to(
            call_session_id,
            StateType.ADVISORY,
            state_data={
                "advisory_id": advisory_id,
                "confidence": confidence,
                "delivered_at": datetime.utcnow().isoformat()
            }
        )
    
    async def escalate_to_expert(
        self,
        call_session_id: int,
        escalation_id: int,
        reason: str
    ):
        """Escalate call to human expert"""
        await self.state_machine.transition_to(
            call_session_id,
            StateType.ESCALATED,
            state_data={
                "escalation_id": escalation_id,
                "reason": reason,
                "escalated_at": datetime.utcnow().isoformat()
            }
        )
    
    async def send_closure_summary(
        self,
        call_session_id: int,
        summary_id: int
    ):
        """Send call summary and close"""
        await self.state_machine.transition_to(
            call_session_id,
            StateType.CLOSURE,
            state_data={
                "summary_id": summary_id,
                "sms_scheduled": True
            }
        )
    
    async def end_call(
        self,
        call_session_id: int,
        reason: str = "completed"
    ):
        """End the call"""
        await self.state_machine.transition_to(
            call_session_id,
            StateType.ENDED,
            state_data={
                "reason": reason,
                "ended_at": datetime.utcnow().isoformat()
            }
        )
    
    async def get_call_status(self, call_session_id: int) -> Dict:
        """Get current call status for frontend/monitoring"""
        current_state = await self.state_machine.get_current_state(call_session_id)
        states_history = await self.state_machine.get_state_history(call_session_id)
        
        return {
            "current_state": current_state.state.value if current_state else None,
            "current_state_data": current_state.state_data if current_state else {},
            "states_visited": [s.state.value for s in states_history],
            "total_duration_seconds": sum([
                await self.state_machine.get_time_in_state(s)
                for s in states_history
            ]),
            "is_active": current_state.state != StateType.ENDED if current_state else False
        }
