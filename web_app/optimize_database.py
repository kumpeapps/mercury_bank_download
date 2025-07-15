"""
Query optimization script for Mercury Bank database.
Adds indexes and optimizes common query patterns.
"""

import os
import sys
import logging
from sqlalchemy import text, create_engine

# Add the app directory to the path
sys.path.append("/app")

from database_config import engine

logger = logging.getLogger(__name__)


def optimize_database():
    """Apply database optimizations including indexes and settings."""

    optimizations = [
        # User table optimizations
        ("idx_users_username", "CREATE INDEX idx_users_username ON users(username)"),
        ("idx_users_created_at", "CREATE INDEX idx_users_created_at ON users(created_at)"),
        
        # Transaction table optimizations (most important for performance)
        ("idx_transactions_account_id", "CREATE INDEX idx_transactions_account_id ON transactions(account_id)"),
        ("idx_transactions_posted_at", "CREATE INDEX idx_transactions_posted_at ON transactions(posted_at)"),
        ("idx_transactions_created_at", "CREATE INDEX idx_transactions_created_at ON transactions(created_at)"),
        ("idx_transactions_account_posted", "CREATE INDEX idx_transactions_account_posted ON transactions(account_id, posted_at DESC)"),
        ("idx_transactions_account_created", "CREATE INDEX idx_transactions_account_created ON transactions(account_id, created_at DESC)"),
        ("idx_transactions_amount", "CREATE INDEX idx_transactions_amount ON transactions(amount)"),
        ("idx_transactions_note", "CREATE INDEX idx_transactions_note ON transactions(note(255))"),
        ("idx_transactions_description", "CREATE INDEX idx_transactions_description ON transactions(description(255))"),
        ("idx_transactions_status", "CREATE INDEX idx_transactions_status ON transactions(status)"),
        
        # Account table optimizations
        ("idx_accounts_mercury_account_id", "CREATE INDEX idx_accounts_mercury_account_id ON accounts(mercury_account_id)"),
        ("idx_accounts_name", "CREATE INDEX idx_accounts_name ON accounts(name)"),
        ("idx_accounts_exclude_reports", "CREATE INDEX idx_accounts_exclude_reports ON accounts(exclude_from_reports)"),
        
        # Mercury account optimizations
        ("idx_mercury_accounts_name", "CREATE INDEX idx_mercury_accounts_name ON mercury_accounts(name)"),
        ("idx_mercury_accounts_is_active", "CREATE INDEX idx_mercury_accounts_is_active ON mercury_accounts(is_active)"),
        ("idx_mercury_accounts_sync_enabled", "CREATE INDEX idx_mercury_accounts_sync_enabled ON mercury_accounts(sync_enabled)"),
        
        # Transaction attachments optimizations
        ("idx_transaction_attachments_transaction_id", "CREATE INDEX idx_transaction_attachments_transaction_id ON transaction_attachments(transaction_id)"),
        
        # User settings optimizations
        ("idx_user_settings_user_id", "CREATE INDEX idx_user_settings_user_id ON user_settings(user_id)"),
        
        # Budget optimizations
        ("idx_budgets_mercury_account_id", "CREATE INDEX idx_budgets_mercury_account_id ON budgets(mercury_account_id)"),
        ("idx_budgets_budget_month", "CREATE INDEX idx_budgets_budget_month ON budgets(budget_month)"),
        ("idx_budgets_is_active", "CREATE INDEX idx_budgets_is_active ON budgets(is_active)"),
        ("idx_budget_categories_budget_id", "CREATE INDEX idx_budget_categories_budget_id ON budget_categories(budget_id)"),
        
        # Composite indexes for common query patterns
        ("idx_transactions_account_posted_amount", "CREATE INDEX idx_transactions_account_posted_amount ON transactions(account_id, posted_at DESC, amount)"),
        ("idx_transactions_note_posted", "CREATE INDEX idx_transactions_note_posted ON transactions(note(100), posted_at DESC)"),
        ("idx_transactions_status_posted", "CREATE INDEX idx_transactions_status_posted ON transactions(status, posted_at DESC)"),
    ]

    print("🔧 Applying database optimizations...")

    with engine.connect() as conn:
        for index_name, optimization in optimizations:
            try:
                # Check if index already exists
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.statistics 
                    WHERE table_schema = DATABASE() 
                    AND index_name = :index_name
                """), {"index_name": index_name}).fetchone()
                
                if result and result[0] > 0:
                    print(f"  ✅ Index already exists: {index_name}")
                    continue
                
                print(f"  Applying: {optimization[:50]}...")
                conn.execute(text(optimization))
                conn.commit()
                print(f"  ✅ Created index: {index_name}")
            except Exception as e:
                print(f"  ⚠️  Warning: {optimization[:50]}... failed: {e}")

    print("✅ Database optimizations applied!")


if __name__ == "__main__":
    optimize_database()
