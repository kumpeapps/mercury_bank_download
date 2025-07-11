#!/usr/bin/env python3
"""
Migration script to ensure the first user is marked as admin.
This script can be run after deployment to fix existing installations.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.user import User
from models.user_settings import UserSettings
from models.role import Role


def ensure_first_user_is_admin():
    """Ensure the first user in the system has admin privileges."""
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
        
        print("Checking user admin status...")
        
        # Get or create admin, super-admin, and user roles
        user_role = Role.get_or_create(session, "user", 
                                       "Basic user with read access to their own data", 
                                       is_system_role=True)
        admin_role = Role.get_or_create(session, "admin", 
                                        "Can manage Mercury accounts and account settings", 
                                        is_system_role=True)
        super_admin_role = Role.get_or_create(session, "super-admin", 
                                             "Full access to all system features including user management and system settings", 
                                             is_system_role=True)
        
        # Check if any users with admin role exist
        admin_count = (
            session.query(User)
            .filter(User.roles.any(Role.name.in_(["admin", "super-admin"])))
            .count()
        )
        
        if admin_count > 0:
            print(f"Found {admin_count} user(s) with admin/super-admin roles. No action needed.")
            return True
        
        print("No users with admin roles found. Looking for first user to promote...")
        
        # Get the first user (oldest by ID)
        first_user = session.query(User).order_by(User.id).first()
        
        if not first_user:
            print("No users found in the system.")
            return True
        
        print(f"Promoting first user '{first_user.username}' to super-admin...")
        
        # Add user role (baseline for all users)
        if user_role not in first_user.roles:
            first_user.roles.append(user_role)
        
        # Add super-admin role to first user
        if super_admin_role not in first_user.roles:
            first_user.roles.append(super_admin_role)
        
        # Also add admin role for extra access
        if admin_role not in first_user.roles:
            first_user.roles.append(admin_role)
        
        # Create user settings if they don't exist
        if not first_user.settings:
            user_settings = UserSettings(user_id=first_user.id)
            session.add(user_settings)
        
        session.commit()
        print(f"✓ User '{first_user.username}' has been promoted to super-admin!")
        return True
        
    except Exception as e:
        print(f"Error ensuring admin user: {str(e)}")
        if 'session' in locals():
            session.rollback()
        return False
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    print("First User Admin Migration")
    print("=" * 30)
    
    success = ensure_first_user_is_admin()
    
    if success:
        print("\n✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
