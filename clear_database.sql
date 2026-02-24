-- Clear All Data from Kisan Vani Database Tables
-- Run this to empty all tables before testing

USE kisanvani_db;

-- Disable foreign key checks temporarily
SET FOREIGN_KEY_CHECKS = 0;

-- Clear all data from tables (in correct order due to foreign keys)
DELETE FROM escalations;
DELETE FROM advisories;
DELETE FROM cases;
DELETE FROM call_sessions;
DELETE FROM farmers;
DELETE FROM kb_entries;
DELETE FROM users WHERE username != 'admin'; -- Keep admin user

-- Reset auto-increment counters
ALTER TABLE escalations AUTO_INCREMENT = 1;
ALTER TABLE advisories AUTO_INCREMENT = 1;
ALTER TABLE cases AUTO_INCREMENT = 1;
ALTER TABLE call_sessions AUTO_INCREMENT = 1;
ALTER TABLE farmers AUTO_INCREMENT = 1;
ALTER TABLE kb_entries AUTO_INCREMENT = 1;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Verify tables are empty
SELECT 'farmers' as table_name, COUNT(*) as count FROM farmers
UNION ALL
SELECT 'call_sessions', COUNT(*) FROM call_sessions
UNION ALL
SELECT 'cases', COUNT(*) FROM cases
UNION ALL
SELECT 'advisories', COUNT(*) FROM advisories
UNION ALL
SELECT 'kb_entries', COUNT(*) FROM kb_entries
UNION ALL
SELECT 'escalations', COUNT(*) FROM escalations;

SELECT '✅ Database cleared successfully!' as status;
