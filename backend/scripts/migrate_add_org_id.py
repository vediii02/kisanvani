"""
Database migration script to add organisation_id column to users table
Run this script if the column doesn't exist
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from db.session import AsyncSessionLocal


async def add_organisation_id_column():
    """Add organisation_id column to users table"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if column exists
            result = await db.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'organisation_id'
            """))
            exists = result.scalar()
            
            if exists:
                print("✅ Column 'organisation_id' already exists in users table")
                return
            
            print("Adding 'organisation_id' column to users table...")
            
            # Add the column
            await db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN organisation_id INT NULL,
                ADD CONSTRAINT fk_users_organisation 
                FOREIGN KEY (organisation_id) 
                REFERENCES organisations(id) 
                ON DELETE SET NULL
            """))
            
            await db.commit()
            
            print("✅ Successfully added 'organisation_id' column to users table")
            print("   - Column: organisation_id INT NULL")
            print("   - Foreign Key: fk_users_organisation -> organisations(id)")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            await db.rollback()
            
            # If error is because column already exists, that's okay
            if "Duplicate column name" in str(e):
                print("✅ Column already exists (migration already applied)")
            else:
                raise


async def verify_migration():
    """Verify the migration was successful"""
    async with AsyncSessionLocal() as db:
        try:
            # Check column exists
            result = await db.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'organisation_id'
            """))
            
            row = result.fetchone()
            
            if row:
                print("\n✅ Migration Verification:")
                print(f"   Column Name: {row[0]}")
                print(f"   Data Type: {row[1]}")
                print(f"   Nullable: {row[2]}")
                print(f"   Key: {row[3] or 'None'}")
                
                # Check foreign key constraint
                result = await db.execute(text("""
                    SELECT CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'users'
                    AND COLUMN_NAME = 'organisation_id'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """))
                
                fk = result.fetchone()
                if fk:
                    print(f"   Foreign Key: {fk[0]} -> {fk[1]}.{fk[2]}")
            else:
                print("❌ Column not found after migration")
                
        except Exception as e:
            print(f"❌ Verification Error: {str(e)}")


if __name__ == "__main__":
    print("="*60)
    print("DATABASE MIGRATION: Add organisation_id to users table")
    print("="*60)
    
    asyncio.run(add_organisation_id_column())
    asyncio.run(verify_migration())
    
    print("\n" + "="*60)
    print("Migration Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Restart the backend: docker-compose restart backend")
    print("2. Create organisation admin: python scripts/create_org_admin.py")
    print("3. Login at http://localhost:3000/login")
