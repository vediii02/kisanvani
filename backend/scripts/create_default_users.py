"""
Create default users for production: superadmin, admin, operator
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from db.models.user import User
from core.config import settings
from core.auth import get_password_hash
from datetime import datetime, timezone

DEFAULT_USERS = [
    {
        "username": "superadmin",
        "email": "superadmin@kisanvani.com",
        "password": "Admin@123",
        "full_name": "Super Administrator",
        "role": "superadmin",
        "phone": "+919999999999"
    },
    {
        "username": "admin",
        "email": "admin@kisanvani.com",
        "password": "Admin@123",
        "full_name": "Administrator",
        "role": "admin",
        "phone": "+919999999998"
    },
    {
        "username": "operator",
        "email": "operator@kisanvani.com",
        "password": "Operator@123",
        "full_name": "Operator User",
        "role": "operator",
        "phone": "+919999999997"
    },
    {
        "username": "org_admin",
        "email": "orgadmin@kisanvani.com",
        "password": "OrgAdmin@123",
        "full_name": "Organisation Admin",
        "role": "organisation_admin",
        "phone": "+919999999996"
    }
]

async def create_default_users():
    """Create default users for production"""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            print("👤 Creating default users for production...")
            
            for user_data in DEFAULT_USERS:
                # Check if user exists
                result = await session.execute(
                    select(User).where(User.username == user_data["username"])
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"  ⚠️  User {user_data['username']} already exists")
                    continue
                
                # Create user
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                )
                
                session.add(user)
                await session.commit()
                
                print(f"  ✅ Created: {user_data['username']} (password: {user_data['password']})")
            
            print("\n🎉 Default users created successfully!")
            print("\n📋 Login credentials:")
            print("=" * 60)
            for user_data in DEFAULT_USERS:
                print(f"  Role: {user_data['role']:20} | Username: {user_data['username']:15} | Password: {user_data['password']}")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_default_users())
