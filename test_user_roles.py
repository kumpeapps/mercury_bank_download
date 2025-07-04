#!/usr/bin/env python3
"""
Test script to verify user role assignments work correctly
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_app.models.user import User
from web_app.models.user_settings import UserSettings
from web_app.models.role import Role


def test_user_role_assignment():
    """Test that users get the correct roles assigned."""
    database_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://mercury_user:mercury_password@localhost:3306/mercury_bank')
    
    try:
        # Create database engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Testing User Role Assignment")
        print("=" * 30)
        
        # Check current user count
        user_count = session.query(User).count()
        print(f"Current user count: {user_count}")
        
        # Check if roles exist
        roles = session.query(Role).all()
        print(f"Available roles: {[role.name for role in roles]}")
        
        # If no users exist, simulate first user creation
        if user_count == 0:
            print("\n🔸 Simulating first user creation...")
            
            # Create test user
            test_user = User(username="testuser", email="test@example.com")
            test_user.set_password("testpassword")
            session.add(test_user)
            session.flush()  # Get user ID
            
            # Get roles
            user_role = Role.get_or_create(session, "user", 
                                         "Basic user with read access to their own data", 
                                         is_system_role=True)
            admin_role = Role.get_or_create(session, "admin", 
                                          "Administrator with full system access", 
                                          is_system_role=True)
            super_admin_role = Role.get_or_create(session, "super-admin", 
                                                "Super administrator with all privileges including user management", 
                                                is_system_role=True)
            
            # Assign roles to first user
            test_user.roles.append(user_role)
            test_user.roles.append(admin_role)
            test_user.roles.append(super_admin_role)
            
            # Create user settings
            user_settings = UserSettings(user_id=test_user.id, is_admin=True)
            session.add(user_settings)
            
            session.commit()
            
            print(f"✅ Created first user '{test_user.username}' with roles: {[role.name for role in test_user.roles]}")
            print(f"✅ User settings is_admin: {test_user.settings.is_admin}")
            
        else:
            # Check existing users and their roles
            print(f"\n🔸 Checking existing users...")
            users = session.query(User).all()
            for user in users:
                print(f"User: {user.username}")
                print(f"  Roles: {[role.name for role in user.roles]}")
                print(f"  is_admin: {user.settings.is_admin if user.settings else 'No settings'}")
                print(f"  is_super_admin property: {user.is_super_admin}")
                print()
                
        return True
        
    except Exception as e:
        print(f"Error testing user roles: {str(e)}")
        if 'session' in locals():
            session.rollback()
        return False
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    success = test_user_role_assignment()
    sys.exit(0 if success else 1)
