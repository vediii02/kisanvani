import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from db.base import AsyncSessionLocal
from sqlalchemy import select
from db.models.user import User
from core.auth import verify_password
import logging

# Mock FastAPI status and HTTPException for the purpose of the test if needed
# but we can just import the logic from the route if we want to be very precise

async def test_login_logic(username, password):
    async with AsyncSessionLocal() as db:
        print(f"Testing login logic for user: {username}")
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user:
            print("  User not found.")
            return

        print(f"  User found. Status: {user.status}")
        
        # Simulating the logic in auth.py
        if user.status == "inactive":
            print("  Login Result: account deactivated please contact organisation for more details")
            return
            
        if not verify_password(password, user.hashed_password):
            print("  Login Result: Incorrect username or password")
        else:
            print("  Login Result: Success")

async def main():
    # We need a user to test with. I'll search for any inactive user first.
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.status == 'inactive'))
        user = result.scalars().first()
        
        if user:
            await test_login_logic(user.username, "any_password")
        else:
            print("No inactive user found to test with.")
            # Let's try to find any active user and simulate deactivation message
            result = await db.execute(select(User).where(User.status == 'active'))
            user = result.scalars().first()
            if user:
                print(f"Simulating deactivation for active user: {user.username}")
                # We won't actually update the DB, just the object in memory for the simulated test
                user.status = 'inactive'
                await test_login_logic(user.username, "any_password")

if __name__ == "__main__":
    asyncio.run(main())
