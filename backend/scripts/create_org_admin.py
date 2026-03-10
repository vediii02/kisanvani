"""
Script to create organisation admin users for companies
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models.user import User
from db.models.organisation import Organisation
from core.auth import get_password_hash


async def create_organisation_admin():
    """Create organisation admin for Rasi Seeds"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if Rasi Seeds organisation exists
            result = await db.execute(
                select(Organisation).where(Organisation.name == "Rasi Seeds")
            )
            rasi_org = result.scalar_one_or_none()
            
            if not rasi_org:
                print("❌ Rasi Seeds organisation not found!")
                print("Please run import_rasi_seeds.py first")
                return
            
            print(f"✅ Found Rasi Seeds organisation (ID: {rasi_org.id})")
            
            # Check if organisation admin already exists
            result = await db.execute(
                select(User).where(User.username == "rasi_admin")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️  User 'rasi_admin' already exists!")
                
                # Update to organisation_admin role
                existing_user.role = "organisation_admin"
                existing_user.organisation_id = rasi_org.id
                await db.commit()
                
                print(f"✅ Updated existing user to organisation_admin role")
                print(f"\n📋 Login Credentials:")
                print(f"   Username: rasi_admin")
                print(f"   Password: [Use existing password or reset]")
                print(f"   Role: organisation_admin")
                print(f"   Organisation: Rasi Seeds (ID: {rasi_org.id})")
                return
            
            # Create new organisation admin user
            new_user = User(
                username="rasi_admin",
                email="admin@rasiseeds.com",
                hashed_password=get_password_hash("rasi123"),
                full_name=rasi_org.name,
                role="organisation_admin",
                organisation_id=rasi_org.id,
                status="active"
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            print("\n✅ Organisation Admin Created Successfully!")
            print("\n" + "="*60)
            print("📋 LOGIN CREDENTIALS")
            print("="*60)
            print(f"Username:     rasi_admin")
            print(f"Password:     rasi123")
            print(f"Email:        admin@rasiseeds.com")
            print(f"Role:         organisation_admin")
            print(f"Organisation: Rasi Seeds (ID: {rasi_org.id})")
            print(f"Full Name:    Rasi Seeds Administrator")
            print("="*60)
            print("\n🔐 IMPORTANT: Change the password after first login!")
            print("\n🌐 Access URL: http://localhost:3000/login")
            print("   After login, navigate to: /org-admin")
            
            # Display organisation stats
            from db.models.brand import Brand
            from db.models.product import Product
            from sqlalchemy import func
            
            brands_count = await db.execute(
                select(func.count(Brand.id)).where(Brand.organisation_id == rasi_org.id)
            )
            products_count = await db.execute(
                select(func.count(Product.id)).where(Product.organisation_id == rasi_org.id)
            )
            
            print(f"\n📊 Organisation Stats:")
            print(f"   Brands: {brands_count.scalar()}")
            print(f"   Products: {products_count.scalar()}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            await db.rollback()
            raise


async def list_organisations():
    """List all organisations"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Organisation))
        orgs = result.scalars().all()
        
        print("\n" + "="*60)
        print("AVAILABLE ORGANISATIONS")
        print("="*60)
        
        if not orgs:
            print("No organisations found!")
            return
        
        for org in orgs:
            print(f"\nID: {org.id}")
            print(f"Name: {org.name}")
            print(f"Domain: {org.domain or 'N/A'}")
            print(f"Phone: {org.phone or 'N/A'}")
            print(f"Active: {'Yes' if org.is_active else 'No'}")
            print(f"Enterprise: {'Yes' if org.is_enterprise else 'No'}")
            print("-" * 60)


async def create_custom_org_admin(org_id: int, username: str, password: str, email: str):
    """Create organisation admin for any organisation"""
    async with AsyncSessionLocal() as db:
        try:
            # Get organisation
            result = await db.execute(
                select(Organisation).where(Organisation.id == org_id)
            )
            org = result.scalar_one_or_none()
            
            if not org:
                print(f"❌ Organisation with ID {org_id} not found!")
                return
            
            print(f"✅ Found organisation: {org.name}")
            
            # Check if username exists
            result = await db.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"❌ Username '{username}' already exists!")
                return
            
            # Create user
            new_user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                full_name=org.name,
                role="organisation_admin",
                organisation_id=org.id,
                status="active"
            )
            
            db.add(new_user)
            await db.commit()
            
            print(f"\n✅ Organisation Admin Created!")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print(f"   Organisation: {org.name} (ID: {org.id})")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            await db.rollback()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create organisation admin users")
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="List all organisations"
    )
    parser.add_argument(
        "--org-id", 
        type=int, 
        help="Organisation ID for custom admin creation"
    )
    parser.add_argument(
        "--username", 
        help="Username for custom admin"
    )
    parser.add_argument(
        "--password", 
        help="Password for custom admin"
    )
    parser.add_argument(
        "--email", 
        help="Email for custom admin"
    )
    
    args = parser.parse_args()
    
    if args.list:
        asyncio.run(list_organisations())
    elif args.org_id and args.username and args.password and args.email:
        asyncio.run(create_custom_org_admin(
            args.org_id, 
            args.username, 
            args.password, 
            args.email
        ))
    else:
        # Default: create Rasi Seeds admin
        asyncio.run(create_organisation_admin())
