#!/bin/bash
# Create test organisation and assign to organisation role user

echo "🏢 Creating Test Organisation"
echo "============================="
echo ""

# Create test organisation
docker exec kisanvani_mysql mysql -ukisanvani -pkisanvani2025 kisanvani_db -e "
INSERT INTO organisations (name, code, business_type, contact_person, contact_email, contact_phone, address, status, created_at, updated_at)
VALUES 
('Rasi Seeds Ltd', 'RASI001', 'Agriculture - Seeds', 'Rajesh Kumar', 'rajesh@rasiseeds.com', '+91 9876543210', 'Hyderabad, Telangana', 'active', NOW(), NOW()),
('Bayer CropScience', 'BAYER001', 'Agriculture - Pesticides', 'Priya Sharma', 'priya@bayer.com', '+91 9876543211', 'Mumbai, Maharashtra', 'active', NOW(), NOW());
" 2>/dev/null

echo "✅ Organisations Created:"
docker exec kisanvani_mysql mysql -ukisanvani -pkisanvani2025 kisanvani_db -e "
SELECT id, name, code, business_type, status FROM organisations;
" 2>/dev/null | grep -v Warning

echo ""
echo "🔗 Assigning Organisation to User..."

# Assign organisation to 'organisation' user
docker exec kisanvani_mysql mysql -ukisanvani -pkisanvani2025 kisanvani_db -e "
UPDATE users 
SET organisation_id = (SELECT id FROM organisations WHERE code='RASI001' LIMIT 1)
WHERE username='organisation';
" 2>/dev/null

echo "✅ User Updated:"
docker exec kisanvani_mysql mysql -ukisanvani -pkisanvani2025 kisanvani_db -e "
SELECT u.username, u.role, u.organisation_id, o.name as org_name 
FROM users u 
LEFT JOIN organisations o ON u.organisation_id = o.id 
WHERE u.username='organisation';
" 2>/dev/null | grep -v Warning

echo ""
echo "📝 Login Credentials for Organisation Role:"
echo "  Username: organisation"
echo "  Password: Admin@123"
echo "  Organisation: Rasi Seeds Ltd"
echo ""
echo "🎯 Now you can:"
echo "  1. Logout and login with 'organisation' user"
echo "  2. Click on 'Companies' in sidebar"
echo "  3. Create and manage companies under Rasi Seeds"
echo ""
