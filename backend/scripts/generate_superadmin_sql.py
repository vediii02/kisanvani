"""
Generate SQL to create super admin user
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("superadmin123")

sql = f"""
-- Insert Super Admin User
INSERT INTO users (username, email, hashed_password, full_name, role, is_active, created_at)
VALUES (
    'superadmin',
    'superadmin@kisanvani.ai',
    '{hashed_password}',
    'Super Administrator',
    'superadmin',
    1,
    NOW()
);

-- Verify the user was created
SELECT id, username, email, full_name, role, is_active 
FROM users 
WHERE username = 'superadmin';
"""

print("="*70)
print("🔐 SUPER ADMIN USER CREATION SQL")
print("="*70)
print(sql)
print("="*70)
print("\n📋 Instructions:")
print("1. Copy the SQL above")
print("2. Connect to your MySQL database")
print("3. Execute the INSERT statement")
print("4. Verify with the SELECT statement")
print("\n🔑 Login Credentials:")
print("   Username: superadmin")
print("   Password: superadmin123")
print("   Email: superadmin@kisanvani.ai")
print("   Role: superadmin")
print("\n⚠️  IMPORTANT: Change the password after first login!")
print("="*70)

# Save to file as well
with open('/home/ubuntu/Desktop/kisan/kisan-main/backend/scripts/superadmin_sql.sql', 'w') as f:
    f.write(sql)
    
print("\n✅ SQL also saved to: backend/scripts/superadmin_sql.sql")
