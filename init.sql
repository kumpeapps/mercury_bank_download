-- Initialize Mercury Bank database
USE mercury_bank;

-- Create indexes for better performance
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_posted_at ON transactions(posted_at);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_accounts_account_number ON accounts(account_number);
CREATE INDEX idx_accounts_status ON accounts(status);

-- Grant additional permissions if needed
GRANT ALL PRIVILEGES ON mercury_bank.* TO 'mercury'@'%';
FLUSH PRIVILEGES;
