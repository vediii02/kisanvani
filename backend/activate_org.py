
import asyncio
from db.session import AsyncSessionLocal
from db.models.organisation import Organisation
from sqlalchemy import update

async def activate_org():
    async with AsyncSessionLocal() as db:
        await db.execute(update(Organisation).where(Organisation.id == 20).values(status='active'))
        await db.commit()
        print('Re-activated Org 20')

if __name__ == "__main__":
    asyncio.run(activate_org())
