-- Migration script to add User and MercuryAccount models
-- Run this script if you have an existing database with accounts and transactions

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create mercury_accounts table
CREATE TABLE IF NOT EXISTS mercury_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    api_key VARCHAR(500) NOT NULL,
    sandbox_mode BOOLEAN DEFAULT FALSE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sync_enabled BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create association table for users and mercury accounts (many-to-many)
CREATE TABLE IF NOT EXISTS user_mercury_accounts (
    user_id INT,
    mercury_account_id INT,
    PRIMARY KEY (user_id, mercury_account_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (mercury_account_id) REFERENCES mercury_accounts(id) ON DELETE CASCADE
);

-- Add mercury_account_id column to existing accounts table
-- First check if the column already exists
SET @column_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'accounts' 
    AND COLUMN_NAME = 'mercury_account_id'
);

-- Add the column only if it doesn't exist
SET @sql = IF(@column_exists = 0,
    'ALTER TABLE accounts ADD COLUMN mercury_account_id INT',
    'SELECT "Column mercury_account_id already exists" as notice'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add foreign key constraint only if it doesn't exist
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'accounts' 
    AND COLUMN_NAME = 'mercury_account_id'
    AND REFERENCED_TABLE_NAME = 'mercury_accounts'
);

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE accounts ADD FOREIGN KEY (mercury_account_id) REFERENCES mercury_accounts(id)',
    'SELECT "Foreign key constraint already exists" as notice'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_accounts_mercury_account_id ON accounts(mercury_account_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_mercury_accounts_active_sync ON mercury_accounts(is_active, sync_enabled);
CREATE INDEX IF NOT EXISTS idx_mercury_accounts_name ON mercury_accounts(name);

-- Update existing accounts to have better indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);
CREATE INDEX IF NOT EXISTS idx_accounts_is_active ON accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_posted_at ON transactions(posted_at);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_type ON transactions(transaction_type);

-- Optional: Create a sample Mercury account (update with your actual API key)
-- INSERT INTO mercury_accounts (name, api_key, sandbox_mode, description, is_active, sync_enabled)
-- VALUES (
--     'My Mercury Account',
--     'your_api_key_here',
--     TRUE,
--     'Main Mercury Bank account for API access',
--     TRUE,
--     TRUE
-- );

-- Optional: Create a sample admin user (update with proper password hash)
-- Note: Use bcrypt to generate a proper password hash
-- Example: python -c "import bcrypt; print(bcrypt.hashpw('your_password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))"
-- INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin, is_active)
-- VALUES (
--     'admin',
--     'admin@company.com',
--     '$2b$12$dummy_hash_replace_with_real_hash',
--     'Admin',
--     'User',
--     TRUE,
--     TRUE
-- );

-- Optional: Associate the sample user with the sample Mercury account
-- INSERT INTO user_mercury_accounts (user_id, mercury_account_id)
-- SELECT u.id, ma.id 
-- FROM users u, mercury_accounts ma 
-- WHERE u.username = 'admin' 
-- AND ma.name = 'My Mercury Account';

-- Display completion message
SELECT 'Migration completed successfully! Remember to:
1. Update Mercury account records with real API keys
2. Create proper password hashes for users
3. Test the synchronization process
4. Review and adjust user permissions' AS notice;
