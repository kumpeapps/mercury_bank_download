-- Migration script to add User and MercuryAccount models
-- Run this script if you have an existing database with accounts and transactions

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
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
    id VARCHAR(255) PRIMARY KEY,
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
    user_id VARCHAR(255),
    mercury_account_id VARCHAR(255),
    PRIMARY KEY (user_id, mercury_account_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (mercury_account_id) REFERENCES mercury_accounts(id) ON DELETE CASCADE
);

-- Add mercury_account_id column to existing accounts table
ALTER TABLE accounts 
ADD COLUMN mercury_account_id VARCHAR(255),
ADD FOREIGN KEY (mercury_account_id) REFERENCES mercury_accounts(id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_accounts_mercury_account_id ON accounts(mercury_account_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_mercury_accounts_active_sync ON mercury_accounts(is_active, sync_enabled);

-- Optional: Create a sample Mercury account (update with your actual API key)
-- INSERT INTO mercury_accounts (id, name, api_key, sandbox_mode, description)
-- VALUES (
--     'sample-mercury-account-1',
--     'My Mercury Account',
--     'your_api_key_here',
--     TRUE,
--     'Main Mercury Bank account for API access'
-- );

-- Optional: Create a sample admin user (update with proper password hash)
-- INSERT INTO users (id, username, email, password_hash, first_name, last_name, is_admin)
-- VALUES (
--     'sample-user-1',
--     'admin',
--     'admin@company.com',
--     '$2b$12$dummy_hash_replace_with_real_hash',
--     'Admin',
--     'User',
--     TRUE
-- );

-- Optional: Associate the sample user with the sample Mercury account
-- INSERT INTO user_mercury_accounts (user_id, mercury_account_id)
-- VALUES ('sample-user-1', 'sample-mercury-account-1');
