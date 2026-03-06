
import asyncio
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models.user import User

async def list_all_users():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"Username: {u.username}, Role: {u.role}, Status: {u.status}, CompID: {u.company_id}")

if __name__ == "__main__":
    asyncio.run(list_all_users())
