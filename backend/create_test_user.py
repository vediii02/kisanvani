
import asyncio
from db.session import AsyncSessionLocal
from db.models.user import User
from db.models.company import Company
from core.auth import get_password_hash

async def create_test_user():
    async with AsyncSessionLocal() as db:
        # Create an inactive company if not exists
        result = await db.execute(select(Company).where(Company.status == 'inactive'))
        company = result.scalars().first()
        if not company:
            company = Company(name="Inactive Co", status="inactive", organisation_id=20)
            db.add(company)
            await db.commit()
            await db.refresh(company)
        
        # Create an active user for this inactive company
        username = "test_active_user_inactive_company"
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                username=username,
                email="test@example.com",
                hashed_password=get_password_hash("password123"),
                role="company",
                company_id=company.id,
                organisation_id=20,
                status="active"
            )
            db.add(user)
            await db.commit()
            print(f"Created user: {username} with company_id: {company.id}")
        else:
            user.status = "active"
            user.company_id = company.id
            await db.commit()
            print(f"Updated user: {username} to be active with company_id: {company.id}")

if __name__ == "__main__":
    from sqlalchemy import select
    asyncio.run(create_test_user())
