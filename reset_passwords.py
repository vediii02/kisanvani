#!/usr/bin/env python3
"""
Script to reset user passwords in the database
"""
import sys
from passlib.context import CryptContext
import pymysql

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Database connection
db_config = {
    'host': 'localhost',
    'port': 3308,  # Docker mapped port
    'user': 'kisanvani',
    'password': 'kisanvani2025',
    'database': 'kisanvani_db'
}

print("🔐 Password Reset Tool")
print("=" * 50)

# Default password
new_password = "Admin@123"
new_hash = get_password_hash(new_password)

print(f"New password will be: {new_password}")
print(f"Hash: {new_hash[:50]}...")
print()

try:
    # Connect to database
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT id, username, email, role FROM users")
    users = cursor.fetchall()
    
    print("Current users:")
    for user in users:
        print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}")
    
    print()
    print(f"Updating all user passwords to: {new_password}")
    
    # Update password for all users
    cursor.execute("UPDATE users SET hashed_password = %s", (new_hash,))
    conn.commit()
    
    print(f"✅ Updated {cursor.rowcount} user(s)")
    print()
    print("You can now login with:")
    for user in users:
        print(f"  Username: {user[1]}, Password: {new_password}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
