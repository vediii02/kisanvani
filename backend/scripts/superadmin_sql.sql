
-- Insert Super Admin User
INSERT INTO users (username, email, hashed_password, full_name, role, is_active, created_at)
VALUES (
    'superadmin',
    'superadmin@kisanvani.ai',
    '$2b$12$P1yvVq1WkQjz70UTzMRGhOaCJxHRN3pGFTLEmea3AfM15ScF1ixsC',
    'Super Administrator',
    'superadmin',
    1,
    NOW()
);

-- Verify the user was created
SELECT id, username, email, full_name, role, is_active 
FROM users 
WHERE username = 'superadmin';
