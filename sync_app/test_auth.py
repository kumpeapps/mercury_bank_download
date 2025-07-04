#!/usr/bin/env python3
"""
Test script to verify authentication and role fixes.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, joinedload
from models.user import User
from models.role import Role

def test_authentication():
    """Test the authentication fixes."""
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        # Create database engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("🔍 Testing authentication fixes...")
        
        # Test 1: Load user with roles (eager loading to avoid DetachedInstanceError)
        print("\n1. Testing eager loading of user roles...")
        user = (session.query(User)
               .options(joinedload(User.roles))
               .filter_by(username='justinkumpe')
               .first())
        
        if user:
            print(f"✅ User '{user.username}' loaded successfully")
            print(f"   Roles: {[role.name for role in user.roles]}")
            
            # Test 2: Check super admin authentication logic
            print("\n2. Testing super admin authentication...")
            super_admin_username = os.environ.get('SUPER_ADMIN_USERNAME')
            print(f"   SUPER_ADMIN_USERNAME env var: {super_admin_username}")
            
            if super_admin_username and user.username == super_admin_username:
                print(f"✅ User '{user.username}' matches SUPER_ADMIN_USERNAME")
            else:
                print(f"⚠️  User '{user.username}' does not match SUPER_ADMIN_USERNAME")
            
            # Test 3: Check role-based authentication
            print("\n3. Testing role-based authentication...")
            has_admin = user.has_role('admin')
            has_super_admin = user.has_role('super-admin')
            print(f"   has_role('admin'): {has_admin}")
            print(f"   has_role('super-admin'): {has_super_admin}")
            
            if has_admin or has_super_admin:
                print("✅ User has admin privileges via roles")
            else:
                print("❌ User does not have admin privileges via roles")
                
            # Test 4: Check legacy admin flag
            print("\n4. Testing legacy admin flag...")
            if hasattr(user, 'settings') and user.settings:
                legacy_admin = user.settings.is_admin
                print(f"   Legacy admin flag: {legacy_admin}")
            else:
                print("   No legacy admin settings found")
                
        else:
            print(f"❌ User 'justinkumpe' not found")
            return False
            
        # Test 5: List all users with roles
        print("\n5. Testing user listing with roles...")
        users = (session.query(User)
                .options(joinedload(User.roles))
                .all())
        
        print(f"✅ Found {len(users)} users:")
        for u in users:
            roles = [role.name for role in u.roles]
            print(f"   {u.username}: {roles}")
            
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during authentication test: {str(e)}")
        if 'session' in locals():
            session.close()
        return False

if __name__ == "__main__":
    print("Authentication Test Script")
    print("=" * 30)
    
    success = test_authentication()
    
    if success:
        print("\n✅ All authentication tests passed!")
    else:
        print("\n❌ Some authentication tests failed!")
    
    sys.exit(0 if success else 1)
