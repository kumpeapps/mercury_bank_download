-- Rollback script for Mercury Bank multi-account migration
-- Use this script to revert the database to single-account mode
-- ⚠️  WARNING: This will delete all user and Mercury account data!

-- Confirm before proceeding
SELECT 'WARNING: This script will delete multi-account data!' AS warning;
SELECT 'Press Ctrl+C to cancel, or continue to proceed...' AS notice;

-- Remove foreign key constraint from accounts table
ALTER TABLE accounts DROP FOREIGN KEY accounts_ibfk_1;

-- Remove mercury_account_id column from accounts table
ALTER TABLE accounts DROP COLUMN mercury_account_id;

-- Drop indexes related to multi-account features
DROP INDEX IF EXISTS idx_accounts_mercury_account_id ON accounts;
DROP INDEX IF EXISTS idx_users_username ON users;
DROP INDEX IF EXISTS idx_users_email ON users;
DROP INDEX IF EXISTS idx_users_is_active ON users;
DROP INDEX IF EXISTS idx_mercury_accounts_active_sync ON mercury_accounts;
DROP INDEX IF EXISTS idx_mercury_accounts_name ON mercury_accounts;

-- Drop association table
DROP TABLE IF EXISTS user_mercury_accounts;

-- Drop mercury_accounts table
DROP TABLE IF EXISTS mercury_accounts;

-- Drop users table
DROP TABLE IF EXISTS users;

-- Display completion message
SELECT 'Rollback completed successfully!' AS status;
SELECT 'You can now use single-account mode with MERCURY_API_KEY environment variable' AS notice;
