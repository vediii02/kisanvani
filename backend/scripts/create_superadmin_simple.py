"""
Simple script to create super admin user directly via SQL
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Direct SQL approach for quick setup
import asyncio
import asyncpg
from passlib.context import CryptContext
from datetime import datetime, timezone

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_superadmin():
    # Database connection from environment or default
    db_url = os.getenv('DATABASE_URL', 'mysql://kisanvani_user:kisanvani_password@localhost:3308/kisanvani_db')
    
    # Parse MySQL URL to get connection params
    # Format: mysql://user:password@host:port/database
    if 'mysql://' in db_url:
        parts = db_url.replace('mysql://', '').split('@')
        user_pass = parts[0].split(':')
        host_port_db = parts[1].split('/')
        host_port = host_port_db[0].split(':')
        
        user = user_pass[0]
        password = user_pass[1]
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 3306
        database = host_port_db[1]
        
        print(f"🔧 Connecting to MySQL database: {database} at {host}:{port}")
        print(f"   User: {user}")
        
        # For MySQL, we need to use aiomysql
        try:
            import aiomysql
            
            # Create connection
            conn = await aiomysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                db=database
            )
            
            async with conn.cursor() as cursor:
                # Check if superadmin exists
                await cursor.execute(
                    "SELECT username, email, role FROM users WHERE username = 'superadmin'"
                )
                result = await cursor.fetchone()
                
                if result:
                    print("✅ Super Admin already exists!")
                    print(f"   Username: {result[0]}")
                    print(f"   Email: {result[1]}")
                    print(f"   Role: {result[2]}")
                else:
                    # Hash password
                    hashed_password = pwd_context.hash("superadmin123")
                    
                    # Insert superadmin
                    await cursor.execute(
                        """INSERT INTO users (username, email, hashed_password, full_name, role, is_active, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (
                            'superadmin',
                            'superadmin@kisanvani.ai',
                            hashed_password,
                            'Super Administrator',
                            'superadmin',
                            True,
                            datetime.now(timezone.utc)
                        )
                    )
                    await conn.commit()
                    
                    print("✅ Super Admin created successfully!")
                    print(f"   Username: superadmin")
                    print(f"   Password: superadmin123")
                    print(f"   Email: superadmin@kisanvani.ai")
                    print(f"   Role: superadmin")
                    print("\n⚠️  IMPORTANT: Please change the password after first login!")
            
            conn.close()
            
        except ImportError:
            print("❌ aiomysql not installed. Installing...")
            os.system("pip3 install aiomysql")
            print("✅ Please run the script again")
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\n💡 Alternative: Run this SQL directly in your MySQL database:")
            print(f"""
INSERT INTO users (username, email, hashed_password, full_name, role, is_active, created_at)
VALUES (
    'superadmin',
    'superadmin@kisanvani.ai',
    '{pwd_context.hash("superadmin123")}',
    'Super Administrator',
    'superadmin',
    1,
    NOW()
);
""")

if __name__ == "__main__":
    print("🔧 Creating Super Admin User...")
    try:
        asyncio.run(create_superadmin())
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Manual SQL Command:")
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash("superadmin123")
        print(f"""
Run this in your MySQL database:

INSERT INTO users (username, email, hashed_password, full_name, role, is_active, created_at)
VALUES (
    'superadmin',
    'superadmin@kisanvani.ai',
    '{hashed}',
    'Super Administrator',
    'superadmin',
    1,
    NOW()
);

Then login with:
Username: superadmin
Password: superadmin123
""")
    print("\n✅ Setup complete!")
