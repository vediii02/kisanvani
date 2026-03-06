
import asyncio
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models.user import User

async def find_nihu():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username.like('%nihu%')))
        users = result.scalars().all()
        if not users:
            print("No users found with 'nihu' in username.")
        for u in users:
            print(f"User: {u.username}, Role: {u.role}, Status: {u.status}, CompID: {u.company_id}")

if __name__ == "__main__":
    asyncio.run(find_nihu())
