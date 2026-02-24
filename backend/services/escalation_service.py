from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.escalation import Escalation, EscalationStatus
from schemas.case import CaseResponse
import logging

logger = logging.getLogger(__name__)

class EscalationService:
    async def create_escalation(
        self,
        db: AsyncSession,
        case_id: int,
        reason: str,
        confidence_score: str
    ) -> Escalation:
        escalation = Escalation(
            case_id=case_id,
            reason=reason,
            confidence_score=confidence_score,
            status=EscalationStatus.PENDING
        )
        db.add(escalation)
        await db.commit()
        await db.refresh(escalation)
        logger.info(f"Created escalation for case {case_id}")
        return escalation
    
    async def get_pending_escalations(self, db: AsyncSession):
        result = await db.execute(
            select(Escalation).where(Escalation.status == EscalationStatus.PENDING)
        )
        return result.scalars().all()

escalation_service = EscalationService()