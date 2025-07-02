-- Add primary_account_id column to user_settings table
-- This allows users to set a default account within their Mercury account

-- Add the primary_account_id column
ALTER TABLE user_settings 
ADD COLUMN primary_account_id VARCHAR(255) NULL 
AFTER primary_mercury_account_id;
