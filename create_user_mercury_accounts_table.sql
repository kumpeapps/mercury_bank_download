-- Create the missing user_mercury_accounts association table
-- This table is required for the many-to-many relationship between users and mercury_accounts

USE Bot_mercury;

-- Create the user_mercury_accounts table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_mercury_accounts (
    user_id INT NOT NULL,
    mercury_account_id INT NOT NULL,
    PRIMARY KEY (user_id, mercury_account_id),
    INDEX idx_user_id (user_id),
    INDEX idx_mercury_account_id (mercury_account_id)
);

-- Add foreign key constraints if the referenced tables exist
-- Note: These will only be added if the users and mercury_accounts tables exist

-- Check if users table exists and add foreign key if it does
SET @users_table_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = 'Bot_mercury' 
    AND TABLE_NAME = 'users'
);

SET @mercury_accounts_table_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = 'Bot_mercury' 
    AND TABLE_NAME = 'mercury_accounts'
);

-- Add foreign key constraint for user_id if users table exists
SET @sql = IF(@users_table_exists > 0,
    'ALTER TABLE user_mercury_accounts ADD CONSTRAINT fk_user_mercury_accounts_user_id 
     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE',
    'SELECT "Users table does not exist - skipping foreign key constraint" as message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add foreign key constraint for mercury_account_id if mercury_accounts table exists  
SET @sql = IF(@mercury_accounts_table_exists > 0,
    'ALTER TABLE user_mercury_accounts ADD CONSTRAINT fk_user_mercury_accounts_mercury_account_id 
     FOREIGN KEY (mercury_account_id) REFERENCES mercury_accounts(id) ON DELETE CASCADE',
    'SELECT "Mercury_accounts table does not exist - skipping foreign key constraint" as message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Show the table structure to confirm creation
DESCRIBE user_mercury_accounts;

SELECT 'user_mercury_accounts table created successfully!' as result;
