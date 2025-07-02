#!/usr/bin/env python3
"""
Test script to validate migration system functionality.
Run this to test if migrations work correctly.
"""

import os
import sys
from migration_manager import MigrationManager

def test_migrations():
    """Test the migration system."""
    print("🧪 Testing migration system...")
    
    database_url = os.environ.get(
        "DATABASE_URL", 
        "mysql+pymysql://user:password@localhost:3306/mercury_bank"
    )
    
    try:
        migration_manager = MigrationManager(database_url)
        
        # Test database connection
        print("🔗 Testing database connection...")
        connection = migration_manager.get_connection()
        connection.close()
        print("✅ Database connection successful")
        
        # Test migration table creation
        print("📋 Testing migration table creation...")
        migration_manager.ensure_migrations_table()
        print("✅ Migration table created/verified")
        
        # Test migration file discovery
        print("📁 Testing migration file discovery...")
        migration_files = migration_manager.get_migration_files()
        print(f"✅ Found {len(migration_files)} migration files: {migration_files}")
        
        # Test executed migrations tracking
        print("📊 Testing executed migrations tracking...")
        executed = migration_manager.get_executed_migrations()
        print(f"✅ Found {len(executed)} executed migrations")
        
        # Run migrations
        print("🔄 Running migrations...")
        success = migration_manager.run_migrations()
        
        if success:
            print("✅ All tests passed! Migration system is working correctly.")
            return True
        else:
            print("❌ Migration execution failed")
            return False
            
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_migrations()
    sys.exit(0 if success else 1)
