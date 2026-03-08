import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import AsyncSessionLocal
from db.models.company import Company
from db.models.call_session import CallSession
from sqlalchemy import select, or_, not_

async def find_mismatched_calls():
    async with AsyncSessionLocal() as db:
        # Test Org ID 1
        org_id = 1
        
        # 1. Get company phones for Org 1
        result = await db.execute(select(Company).where(Company.organisation_id == org_id))
        company = result.scalar_one_or_none()
        
        if not company:
            print(f"No company found for Org {org_id}")
            return
            
        print(f"Company: {company.name}")
        print(f"Phones: {company.phone}, {company.secondary_phone}")
        
        phones_to_match = []
        if company.phone:
            phones_to_match.append(company.phone)
            clean_phone = company.phone.lstrip('+')
            phones_to_match.append(f"%{clean_phone[-10:]}") 
        if company.secondary_phone:
            clean_sec = company.secondary_phone.lstrip('+')
            phones_to_match.append(f"%{clean_sec[-10:]}")
            
        # 2. Find calls that have org_id=1 but DON'T match the phones
        phone_conditions = []
        for p in phones_to_match:
            phone_conditions.append(CallSession.to_phone.like(p))
            phone_conditions.append(CallSession.from_phone.like(p))
            
        mismatch_query = select(CallSession).where(
            CallSession.organisation_id == org_id,
            not_(or_(*phone_conditions))
        )
        
        mismatch_result = await db.execute(mismatch_query)
        mismatched_calls = mismatch_result.scalars().all()
        
        print(f"\nFound {len(mismatched_calls)} calls with matching Org ID but NO phone match:")
        for call in mismatched_calls:
            print(f"ID: {call.id}, From: {call.from_phone}, To: {call.to_phone}, Created: {call.created_at}")

if __name__ == "__main__":
    asyncio.run(find_mismatched_calls())
