
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import AsyncSessionLocal
from db.models.user import User
from db.models.company import Company
from db.models.organisation import Organisation

async def verify_login_logic():
    async with AsyncSessionLocal() as db:
        # 1. Test Inactive User
        print("--- Testing Inactive User ---")
        user = User(username="test_inactive_user", status="inactive")
        is_inactive = user.status == "inactive"
        print(f"User status: {user.status} -> is_inactive: {is_inactive}")
        
        # 2. Test Active User with Inactive Company
        print("\n--- Testing Inactive Company ---")
        # Find an inactive company
        result = await db.execute(select(Company).where(Company.status == 'inactive'))
        company = result.scalars().first()
        
        if not company:
            print("No inactive company found in DB. Creating a mock check...")
            company = Company(id=999, status="inactive")
            user = User(username="test_company_user", status="active", company_id=999)
        else:
            print(f"Found inactive company: {company.name} (ID: {company.id})")
            user = User(username="test_company_user", status="active", company_id=company.id)

        is_inactive_final = user.status == "inactive"
        if not is_inactive_final and user.company_id:
            # Replicating the logic in auth.py
            comp_check = await db.get(Company, user.company_id)
            if comp_check and comp_check.status == "inactive":
                is_inactive_final = True
        
        print(f"User status: {user.status}, Company status: {company.status} -> is_inactive_final: {is_inactive_final}")

        # 3. Test Active User with Inactive Organisation
        print("\n--- Testing Inactive Organisation ---")
        # Find an inactive organisation
        result = await db.execute(select(Organisation).where(Organisation.status == 'inactive'))
        org = result.scalars().first()
        
        if not org:
            print("No inactive organisation found in DB. Creating a mock check...")
            org = Organisation(id=888, status="inactive")
            user = User(username="test_org_user", status="active", organisation_id=888)
        else:
            print(f"Found inactive organisation: {org.name} (ID: {org.id})")
            user = User(username="test_org_user", status="active", organisation_id=org.id)

        is_inactive_final = user.status == "inactive"
        if not is_inactive_final and user.organisation_id:
            # Replicating the logic in auth.py
            org_check = await db.get(Organisation, user.organisation_id)
            if org_check and org_check.status == "inactive":
                is_inactive_final = True
        
        print(f"User status: {user.status}, Org status: {org.status} -> is_inactive_final: {is_inactive_final}")

        if is_inactive_final:
            print("\nRESULT: Logic correctly identifies deactivated account!")
        else:
            print("\nRESULT: Logic FAILED to identify deactivated account.")

if __name__ == "__main__":
    asyncio.run(verify_login_logic())
