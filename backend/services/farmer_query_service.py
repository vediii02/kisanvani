from sqlalchemy.ext.asyncio import AsyncSession
from db.models.farmer_query import FarmerQuery
from db.models.farmer_questions import FarmerQuestion

class FarmerQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_query(self, call_session_id, farmer_id, organisation_id,company_id, question, answer, intent=None):
        # query = FarmerQuery(
        #     call_session_id=call_session_id,
        #     farmer_id=farmer_id,
        #     organisation_id=organisation_id,
        #     question=question,
        #     answer=answer,
        #     intent=intent
        # )
        query = FarmerQuestion(
            call_sid=call_session_id,
            farmer_id=farmer_id,
            organisation_id=organisation_id,
            company_id=company_id,
            question_text=question,
            answer_text=answer,
            # intent=intent
        )
        
        self.db.add(query)
        await self.db.commit()
        
        await self.db.refresh(query)
        return query
