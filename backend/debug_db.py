
import asyncio
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models.user import User
from db.models.company import Company
from db.models.organisation import Organisation

async def debug_users():
    async with AsyncSessionLocal() as db:
        print(f"{'Username':<30} | {'Role':<12} | {'User Stat':<10} | {'Comp ID':<7} | {'Comp Stat':<10} | {'Org ID':<7} | {'Org Stat':<10}")
        print("-" * 110)
        
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        for user in users:
            comp_stat = "N/A"
            if user.company_id:
                comp = await db.get(Company, user.company_id)
                comp_stat = comp.status if comp else "NOT FOUND"
                
            org_stat = "N/A"
            if user.organisation_id:
                org = await db.get(Organisation, user.organisation_id)
                org_stat = org.status if org else "NOT FOUND"
                
            print(f"{user.username:<30} | {user.role:<12} | {user.status:<10} | {str(user.company_id):<7} | {comp_stat:<10} | {str(user.organisation_id):<7} | {org_stat:<10}")

if __name__ == "__main__":
    asyncio.run(debug_users())
