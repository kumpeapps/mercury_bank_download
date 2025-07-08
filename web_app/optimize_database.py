"""
Query optimization script for Mercury Bank database.
Adds indexes and optimizes common query patterns.
"""

import os
import sys
import logging
from sqlalchemy import text, create_engine

# Add the app directory to the path
sys.path.append('/app')

from database_config import engine

logger = logging.getLogger(__name__)

def optimize_database():
    """Apply database optimizations including indexes and settings."""
    
    optimizations = [
        # User table optimizations
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
        
        # Transaction table optimizations (most important for performance)
        "CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_transaction_date ON transactions(transaction_date)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_account_date ON transactions(account_id, transaction_date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(amount)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_description ON transactions(description)",
        
        # Account table optimizations
        "CREATE INDEX IF NOT EXISTS idx_accounts_mercury_account_id ON accounts(mercury_account_id)",
        "CREATE INDEX IF NOT EXISTS idx_accounts_name ON accounts(name)",
        "CREATE INDEX IF NOT EXISTS idx_accounts_exclude_reports ON accounts(exclude_from_reports)",
        
        # Mercury account optimizations
        "CREATE INDEX IF NOT EXISTS idx_mercury_accounts_name ON mercury_accounts(name)",
        "CREATE INDEX IF NOT EXISTS idx_mercury_accounts_status ON mercury_accounts(status)",
        
        # Transaction attachments optimizations
        "CREATE INDEX IF NOT EXISTS idx_transaction_attachments_transaction_id ON transaction_attachments(transaction_id)",
        
        # User settings optimizations
        "CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)",
        
        # Budget optimizations
        "CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON budgets(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_budgets_start_date ON budgets(start_date)",
        "CREATE INDEX IF NOT EXISTS idx_budget_categories_budget_id ON budget_categories(budget_id)",
        
        # Composite indexes for common query patterns
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_account_date ON transactions(account_id, transaction_date DESC, amount)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_category_date ON transactions(category, transaction_date DESC)",
        
        # Optimize MySQL settings for better performance
        "SET GLOBAL innodb_flush_log_at_trx_commit = 2",
        "SET GLOBAL sync_binlog = 0",
        "SET GLOBAL innodb_doublewrite = 0",
    ]
    
    print("🔧 Applying database optimizations...")
    
    with engine.connect() as conn:
        for optimization in optimizations:
            try:
                print(f"  Applying: {optimization[:50]}...")
                conn.execute(text(optimization))
                conn.commit()
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print(f"  ✅ Index already exists: {optimization[:50]}...")
                else:
                    print(f"  ⚠️  Warning: {optimization[:50]}... failed: {e}")
    
    print("✅ Database optimizations applied!")

if __name__ == "__main__":
    optimize_database()
