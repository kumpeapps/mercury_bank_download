-- Hot fix for production database table creation order
-- Run this directly on the production MySQL database

-- First, check if tables exist and drop them if they do (be careful!)
-- Only run the DROP statements if you're sure the database is empty/new

-- Create tables in correct order to avoid foreign key constraints

-- 1. Create base tables without foreign key dependencies
CREATE TABLE IF NOT EXISTS users (
    id INTEGER NOT NULL AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (username),
    UNIQUE KEY (email)
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (name)
);

CREATE TABLE IF NOT EXISTS mercury_accounts (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    sandbox_mode BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sync_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_sync_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER NOT NULL AUTO_INCREMENT,
    key_name VARCHAR(255) NOT NULL,
    value TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (key_name)
);

-- 2. Create user-role association table
CREATE TABLE IF NOT EXISTS user_role_association (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE
);

-- 3. Create accounts table (needs to come before user_settings)
CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(255) NOT NULL,
    mercury_account_id INTEGER,
    name VARCHAR(255) NOT NULL,
    account_number VARCHAR(255),
    routing_number VARCHAR(255),
    account_type VARCHAR(100),
    status VARCHAR(100),
    balance FLOAT,
    available_balance FLOAT,
    currency VARCHAR(10) DEFAULT 'USD',
    kind VARCHAR(100),
    nickname VARCHAR(255),
    legal_business_name VARCHAR(255),
    receipt_required VARCHAR(20) DEFAULT 'none',
    receipt_threshold FLOAT,
    receipt_required_deposits VARCHAR(20) DEFAULT 'none',
    receipt_threshold_deposits FLOAT,
    receipt_required_charges VARCHAR(20) DEFAULT 'none',
    receipt_threshold_charges FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (mercury_account_id) REFERENCES mercury_accounts (id)
);

-- 4. Now create user_settings (depends on both users and accounts)
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER NOT NULL AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    primary_mercury_account_id INTEGER,
    primary_account_id VARCHAR(255),
    dashboard_preferences JSON,
    report_preferences JSON,
    transaction_preferences JSON,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (primary_mercury_account_id) REFERENCES mercury_accounts (id),
    FOREIGN KEY (primary_account_id) REFERENCES accounts (id)
);

-- 5. Create remaining tables
CREATE TABLE IF NOT EXISTS user_mercury_account_association (
    user_id INTEGER NOT NULL,
    mercury_account_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, mercury_account_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (mercury_account_id) REFERENCES mercury_accounts (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    amount FLOAT,
    description TEXT,
    posted_at DATETIME,
    status VARCHAR(100),
    transaction_type VARCHAR(100),
    counterparty_name VARCHAR(255),
    counterparty_id VARCHAR(255),
    fee_amount FLOAT,
    fee_description TEXT,
    mercury_category VARCHAR(255),
    user_notes TEXT,
    receipt_required BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (account_id) REFERENCES accounts (id)
);

CREATE TABLE IF NOT EXISTS transaction_attachments (
    id INTEGER NOT NULL AUTO_INCREMENT,
    transaction_id VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    content_type VARCHAR(100),
    file_size INTEGER,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER,
    s3_key VARCHAR(500),
    url VARCHAR(500),
    url_expires_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY (transaction_id) REFERENCES transactions (id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS user_account_access (
    user_id INTEGER NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    access_level VARCHAR(50) DEFAULT 'read',
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER,
    PRIMARY KEY (user_id, account_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users (id)
);

-- Insert default roles
INSERT IGNORE INTO roles (name, description) VALUES 
('user', 'Basic user with read access'),
('admin', 'Administrator with full access'),
('super-admin', 'Super administrator with system-level access'),
('locked', 'Locked user role - prevents login');

-- Mark the migration as completed
INSERT IGNORE INTO system_settings (key_name, value, description) VALUES
('migration_001_baseline_schema_completed', 'true', 'Baseline schema migration completed manually');
