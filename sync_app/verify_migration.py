#!/usr/bin/env python3
"""
Migration Verification Script

This script verifies that the Mercury Bank database migration has been
completed successfully and provides diagnostic information.
"""

import sys
from models import User, MercuryAccount, Account, Transaction
from models.base import create_engine_and_session
from sqlalchemy import text
from sqlalchemy.orm import Session


def check_table_exists(db: Session, table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        result = db.execute(text(f"SHOW TABLES LIKE '{table_name}'"))
        return result.rowcount > 0
    except Exception:
        return False


def check_column_exists(db: Session, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        result = db.execute(text(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = '{table_name}' 
            AND COLUMN_NAME = '{column_name}'
        """))
        return result.scalar() > 0
    except Exception:
        return False


def check_foreign_key_exists(db: Session, table_name: str, column_name: str, referenced_table: str) -> bool:
    """Check if a foreign key constraint exists."""
    try:
        result = db.execute(text(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = '{table_name}' 
            AND COLUMN_NAME = '{column_name}'
            AND REFERENCED_TABLE_NAME = '{referenced_table}'
        """))
        return result.scalar() > 0
    except Exception:
        return False


def check_index_exists(db: Session, table_name: str, index_name: str) -> bool:
    """Check if an index exists."""
    try:
        result = db.execute(text(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = '{table_name}' 
            AND INDEX_NAME = '{index_name}'
        """))
        return result.scalar() > 0
    except Exception:
        return False


def verify_migration() -> bool:
    """Verify the migration status."""
    print("🔍 Mercury Bank Migration Verification")
    print("=" * 50)
    
    try:
        engine, session_local = create_engine_and_session()
        db = session_local()
        
        all_checks_passed = True
        
        # Check core tables
        print("\n📋 Checking Tables:")
        tables = [
            ('users', 'User management table'),
            ('mercury_accounts', 'Mercury account groups table'),
            ('user_mercury_accounts', 'User-Mercury account association table'),
            ('accounts', 'Bank accounts table'),
            ('transactions', 'Transactions table')
        ]
        
        for table_name, description in tables:
            exists = check_table_exists(db, table_name)
            status = "✅" if exists else "❌"
            print(f"   {status} {table_name}: {description}")
            if not exists and table_name in ['users', 'mercury_accounts', 'user_mercury_accounts']:
                all_checks_passed = False
        
        # Check key columns
        print("\n🔗 Checking Key Columns:")
        columns = [
            ('accounts', 'mercury_account_id', 'Foreign key to mercury_accounts'),
            ('users', 'username', 'User login name'),
            ('users', 'password_hash', 'Hashed password'),
            ('mercury_accounts', 'api_key', 'Mercury API key'),
            ('mercury_accounts', 'sandbox_mode', 'Sandbox mode flag')
        ]
        
        for table_name, column_name, description in columns:
            exists = check_column_exists(db, table_name, column_name)
            status = "✅" if exists else "❌"
            print(f"   {status} {table_name}.{column_name}: {description}")
            if not exists:
                all_checks_passed = False
        
        # Check foreign keys
        print("\n🔐 Checking Foreign Key Constraints:")
        foreign_keys = [
            ('accounts', 'mercury_account_id', 'mercury_accounts'),
            ('user_mercury_accounts', 'user_id', 'users'),
            ('user_mercury_accounts', 'mercury_account_id', 'mercury_accounts')
        ]
        
        for table_name, column_name, referenced_table in foreign_keys:
            if check_table_exists(db, table_name) and check_table_exists(db, referenced_table):
                exists = check_foreign_key_exists(db, table_name, column_name, referenced_table)
                status = "✅" if exists else "⚠️"
                print(f"   {status} {table_name}.{column_name} -> {referenced_table}")
        
        # Check indexes
        print("\n📊 Checking Performance Indexes:")
        indexes = [
            ('accounts', 'idx_accounts_mercury_account_id'),
            ('users', 'idx_users_username'),
            ('users', 'idx_users_email'),
            ('mercury_accounts', 'idx_mercury_accounts_active_sync')
        ]
        
        for table_name, index_name in indexes:
            if check_table_exists(db, table_name):
                exists = check_index_exists(db, table_name, index_name)
                status = "✅" if exists else "⚠️"
                print(f"   {status} {index_name}")
        
        # Check data integrity
        print("\n📈 Checking Data Integrity:")
        try:
            user_count = db.query(User).count()
            mercury_account_count = db.query(MercuryAccount).count()
            account_count = db.query(Account).count()
            transaction_count = db.query(Transaction).count()
            
            print(f"   ✅ Users: {user_count}")
            print(f"   ✅ Mercury Accounts: {mercury_account_count}")
            print(f"   ✅ Bank Accounts: {account_count}")
            print(f"   ✅ Transactions: {transaction_count}")
            
            # Check for orphaned accounts
            orphaned_accounts = db.execute(text("""
                SELECT COUNT(*) FROM accounts 
                WHERE mercury_account_id IS NOT NULL 
                AND mercury_account_id NOT IN (SELECT id FROM mercury_accounts)
            """)).scalar()
            
            if orphaned_accounts > 0:
                print(f"   ⚠️  Orphaned accounts: {orphaned_accounts}")
                all_checks_passed = False
            else:
                print("   ✅ No orphaned accounts found")
                
        except Exception as e:
            print(f"   ❌ Error checking data: {e}")
            all_checks_passed = False
        
        db.close()
        
        # Summary
        print("\n" + "=" * 50)
        if all_checks_passed:
            print("🎉 Migration verification PASSED!")
            print("   Your database is ready for multi-account mode.")
            return True
        else:
            print("⚠️  Migration verification found issues.")
            print("   Please review the items marked with ❌ above.")
            print("   You may need to run migration.sql or fix data issues.")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False


def main():
    """Main verification function."""
    success = verify_migration()
    
    if success:
        print("\n📚 Next Steps:")
        print("   1. Run: python setup_db.py (to create initial data)")
        print("   2. Update Mercury account API keys")
        print("   3. Start the sync service")
    else:
        print("\n🔧 Troubleshooting:")
        print("   1. Run: mysql -u username -p database_name < migration.sql")
        print("   2. Check database permissions")
        print("   3. Review migration.sql for any errors")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
