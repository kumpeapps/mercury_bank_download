-- Fix account table schema to remove unique constraint from account_number
-- and allow NULL values since Mercury API doesn't provide account numbers

ALTER TABLE accounts DROP INDEX account_number;
ALTER TABLE accounts MODIFY COLUMN account_number VARCHAR(255) NULL;

-- Clean up any existing accounts with empty account_number values
UPDATE accounts SET account_number = NULL WHERE account_number = '';
