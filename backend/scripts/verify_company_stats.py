import asyncio
import sys
import os

# Add parent directory to path to import db and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import AsyncSessionLocal
from db.models.company import Company
from db.models.brand import Brand
from db.models.product import Product
from db.models.call_session import CallSession
from db.models.call_summary import CallSummary
from sqlalchemy import select, func, or_

async def verify_stats():
    async with AsyncSessionLocal() as db:
        # 1. Get a company to test with
        result = await db.execute(select(Company).limit(1))
        company = result.scalar_one_or_none()
        
        if not company:
            print("No companies found to test with.")
            return
            
        print(f"Testing stats for Company: {company.name} (ID: {company.id}, Org ID: {company.organisation_id})")
        
        # 2. Count Companies in Org
        all_companies_result = await db.execute(select(func.count(Company.id)).where(Company.organisation_id == company.organisation_id))
        is_single_company = all_companies_result.scalar() == 1
        print(f"Is single company in organisation: {is_single_company}")

        # 3. Count Brands
        brand_count = await db.execute(select(func.count(Brand.id)).where(Brand.company_id == company.id))
        print(f"Total Brands: {brand_count.scalar()}")
        
        # 4. Count Products
        product_count = await db.execute(select(func.count(Product.id)).where(Product.company_id == company.id))
        print(f"Total Products: {product_count.scalar()}")
        
        # 5. Count Calls and Queries
        total_calls = 0
        total_queries = 0

        if is_single_company:
            calls_query = select(func.count(CallSession.id)).where(CallSession.organisation_id == company.organisation_id)
            calls_result = await db.execute(calls_query)
            total_calls = calls_result.scalar() or 0
            
            queries_query = select(func.count(CallSummary.id)).join(
                CallSession, CallSession.id == CallSummary.call_session_id
            ).where(CallSession.organisation_id == company.organisation_id)
            queries_result = await db.execute(queries_query)
            total_queries = queries_result.scalar() or 0
        else:
            phones_to_match = []
            if company.phone:
                phones_to_match.append(company.phone)
                clean_phone = company.phone.lstrip('+')
                phones_to_match.append(f"%{clean_phone[-10:]}") 
            if company.secondary_phone:
                clean_sec = company.secondary_phone.lstrip('+')
                phones_to_match.append(f"%{clean_sec[-10:]}")
                
            if phones_to_match:
                phone_conditions = []
                for p in phones_to_match:
                    phone_conditions.append(CallSession.to_phone.like(p))
                    phone_conditions.append(CallSession.from_phone.like(p))
                    
                calls_query = select(func.count(CallSession.id)).where(
                    CallSession.organisation_id == company.organisation_id,
                    or_(*phone_conditions)
                )
                calls_result = await db.execute(calls_query)
                total_calls = calls_result.scalar() or 0
                
                queries_query = select(func.count(CallSummary.id)).join(
                    CallSession, CallSession.id == CallSummary.call_session_id
                ).where(
                    CallSession.organisation_id == company.organisation_id,
                    or_(*phone_conditions)
                )
                queries_result = await db.execute(queries_query)
                total_queries = queries_result.scalar() or 0
        
        print(f"Total Calls: {total_calls}")
        print(f"Total Queries (Call Summaries): {total_queries}")

if __name__ == "__main__":
    asyncio.run(verify_stats())
