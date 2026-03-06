
import asyncio
from db.session import AsyncSessionLocal
from db.models.user import User
from sqlalchemy import select

async def rename_user():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == 'nihu@gmail.com'))
        user = result.scalar_one_or_none()
        if user:
            user.username = 'nihu02'
            print(f"Renamed {user.email} to {user.username}")
            await db.commit()
        else:
            print("User nihu@gmail.com not found")

if __name__ == "__main__":
    asyncio.run(rename_user())
