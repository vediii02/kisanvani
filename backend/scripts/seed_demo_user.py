import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_demo_user():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://mongodb:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client['kisanvani_demo']
    
    # Check if user exists
    existing = await db.users.find_one({"username": "admin"})
    if existing:
        print("Demo user already exists")
        return
    
    # Create demo user
    demo_user = {
        "username": "admin",
        "email": "admin@kisanvani.com",
        "password": pwd_context.hash("admin123"),
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(demo_user)
    print("✅ Demo user created:")
    print("   Username: admin")
    print("   Password: admin123")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_demo_user())
