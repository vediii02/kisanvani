
import asyncio
from sqlalchemy import select, or_
from db.session import AsyncSessionLocal
from db.models.user import User

async def find_nihu_deep():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(
                or_(
                    User.username.like('%nihu%'),
                    User.email.like('%nihu%')
                )
            )
        )
        users = result.scalars().all()
        if not users:
            print("No users found with 'nihu' in username or email.")
        for u in users:
            print(f"Username: {u.username}, Email: {u.email}, Role: {u.role}, Status: {u.status}, CompID: {u.company_id}")

if __name__ == "__main__":
    asyncio.run(find_nihu_deep())
