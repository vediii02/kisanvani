"""
Seed a super admin user for the Kisan Vani AI system.
Run this script to create a super admin account.
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.base import AsyncSessionLocal
from db.models.user import User
from core.auth import get_password_hash

async def seed_superadmin():
    """Create a super admin user."""
    
    # Get database session
    async with AsyncSessionLocal() as db:
        # Check if superadmin already exists
        result = await db.execute(
            select(User).where(User.username == "superadmin")
        )
        existing_superadmin = result.scalar_one_or_none()
        
        if existing_superadmin:
            print("✅ Super Admin already exists!")
            print(f"   Username: {existing_superadmin.username}")
            print(f"   Email: {existing_superadmin.email}")
            print(f"   Role: {existing_superadmin.role}")
            return
        
        # Create superadmin user
        superadmin = User(
            username="superadmin",
            email="superadmin@kisanvani.ai",
            hashed_password=get_password_hash("superadmin123"),
            full_name="Super Administrator",
            role="superadmin",
            is_active=True
        )
        
        db.add(superadmin)
        await db.commit()
        await db.refresh(superadmin)
        
        print("✅ Super Admin created successfully!")
        print(f"   Username: superadmin")
        print(f"   Password: superadmin123")
        print(f"   Email: superadmin@kisanvani.ai")
        print(f"   Role: superadmin")
        print("\n⚠️  IMPORTANT: Please change the password after first login!")

if __name__ == "__main__":
    print("🔧 Seeding Super Admin User...")
    asyncio.run(seed_superadmin())
    print("\n✅ Super Admin seeding complete!")
