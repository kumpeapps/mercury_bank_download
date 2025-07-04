#!/usr/bin/env python3
"""
Test script to verify all roles exist and are accessible.
"""

import os
import sys

# Add sync_app to path to import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sync_app'))

from models.base import create_engine_and_session
from models.role import Role


def verify_roles():
    """Verify all expected roles exist."""
    print("🔍 Verifying System Roles")
    print("=" * 30)
    
    expected_roles = [
        "user",
        "admin", 
        "super-admin",
        "reports",
        "transactions",
        "locked"
    ]
    
    try:
        engine, SessionLocal = create_engine_and_session()
        session = SessionLocal()
        
        # Get all roles from database
        all_roles = session.query(Role).all()
        role_names = [role.name for role in all_roles]
        
        print(f"📊 Found {len(all_roles)} roles in database:")
        for role in all_roles:
            print(f"   ✅ {role.name}: {role.description}")
            print(f"      System Role: {role.is_system_role}")
        
        print(f"\n🔍 Checking for expected roles:")
        all_found = True
        for expected_role in expected_roles:
            if expected_role in role_names:
                print(f"   ✅ {expected_role} - Found")
            else:
                print(f"   ❌ {expected_role} - Missing")
                all_found = False
        
        if all_found:
            print(f"\n✅ All {len(expected_roles)} expected roles are present!")
        else:
            print(f"\n❌ Some expected roles are missing!")
            
        return all_found
        
    except Exception as e:
        print(f"❌ Error verifying roles: {e}")
        return False
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    success = verify_roles()
    sys.exit(0 if success else 1)
