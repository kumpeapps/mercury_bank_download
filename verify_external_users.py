#!/usr/bin/env python3
"""
External User Management Verification Script
Checks whether the USERS_EXTERNALLY_MANAGED environment variable is being properly applied.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import argparse

# Get the database URL from environment variable or use a default
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "mysql+pymysql://mercury_user:mercury_password@mysql:3306/mercury_db"
)

def check_system_settings():
    """Check the system_settings table to verify the externally managed setting."""
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        
        # Check if users_externally_managed exists in system_settings
        query = text("SELECT `key`, `value` FROM system_settings WHERE `key` = 'users_externally_managed'")
        result = db_session.execute(query).fetchone()
        
        if result:
            print(f"✅ Found users_externally_managed in database with value: {result[1]}")
            if result[1].lower() in ('true', '1', 'yes'):
                print("✅ Database setting shows users are externally managed")
            else:
                print("❌ Database setting shows users are NOT externally managed")
        else:
            print("❌ Could not find users_externally_managed in system_settings table")
            
        # Check if signup is enabled
        query = text("SELECT `key`, `value` FROM system_settings WHERE `key` = 'registration_enabled'")
        result = db_session.execute(query).fetchone()
        
        if result:
            print(f"✅ Found registration_enabled in database with value: {result[1]}")
            if result[1].lower() in ('false', '0', 'no'):
                print("✅ Registration is disabled, as expected with external management")
            else:
                print("❌ Registration is enabled, which conflicts with external management")
        else:
            print("❌ Could not find registration_enabled in system_settings table")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        db_session.close()

def main():
    # Check environment variable
    users_externally_managed = os.environ.get("USERS_EXTERNALLY_MANAGED", "false").lower() == "true"
    print(f"\n🔍 USERS_EXTERNALLY_MANAGED environment variable is set to: {users_externally_managed}")
    
    if not users_externally_managed:
        print("\n❌ USERS_EXTERNALLY_MANAGED is not set to 'true' in the environment")
        print("   This is the likely cause of the issue")
        print("   Make sure it's correctly set in your environment or docker-compose.yml")
        
    # Check database settings
    print("\n🔍 Checking database system_settings table:")
    check_system_settings()
    
    print("\n🔍 Verification complete")
    print("If there are discrepancies, restart the web-app service after confirming")
    print("the environment variable is correctly set in docker-compose.yml")

if __name__ == "__main__":
    main()
