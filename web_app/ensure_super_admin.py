#!/usr/bin/env python3
"""
Super Admin Promotion Script

This script runs on container startup to ensure that if a SUPER_ADMIN_USERNAME
environment variable is set, that user is always promoted to admin status.
This provides a reliable way to ensure admin access even if the database
is reset or users are modified.
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


def ensure_super_admin():
    """Ensure the super admin user (if specified) has admin privileges."""
    super_admin_username = os.environ.get('SUPER_ADMIN_USERNAME')
    
    if not super_admin_username:
        # No super admin specified, nothing to do
        return True
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Warning: DATABASE_URL environment variable not found")
        return False
    
    try:
        # Create database engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print(f"Checking super admin user: {super_admin_username}")
        
        # Find the specified user
        user = session.query(User).filter_by(username=super_admin_username).first()
        
        if not user:
            print(f"Super admin user '{super_admin_username}' not found in database")
            print("User must be created first through registration or admin tools")
            return True  # Not an error - user just doesn't exist yet
        
        # Get or create the super-admin, admin, and user roles
        user_role = Role.get_or_create(session, "user", 
                                     "Basic user with read access to their own data", 
                                     is_system_role=True)
        admin_role = Role.get_or_create(session, "admin", 
                                       "Can manage Mercury accounts and account settings", 
                                       is_system_role=True)
        super_admin_role = Role.get_or_create(session, "super-admin", 
                                            "Full access to all system features including user management and system settings", 
                                            is_system_role=True)
        
        # Check if user already has super-admin role
        if user.is_super_admin:
            print(f"✓ User '{super_admin_username}' already has super-admin role")
            
            # Ensure user also has the basic "user" role (all users should have this)
            if user_role not in user.roles:
                user.roles.append(user_role)
                session.commit()
                print(f"✓ Added user role to '{super_admin_username}'")
            
            # Ensure user has settings
            if not user.settings:
                user_settings = UserSettings(user_id=user.id)
                session.add(user_settings)
                session.commit()
                print(f"✓ Created user settings for '{super_admin_username}'")
                
            return True
        
        print(f"Promoting user '{super_admin_username}' to super-admin...")
        
        # Add user role (baseline for all users)
        if user_role not in user.roles:
            user.roles.append(user_role)
            
        # Add super-admin role if not already present
        if super_admin_role not in user.roles:
            user.roles.append(super_admin_role)
        
        # Also add admin role for extra access
        if admin_role not in user.roles:
            user.roles.append(admin_role)
        
        # Ensure user has settings
        if not user.settings:
            user_settings = UserSettings(user_id=user.id)
            session.add(user_settings)
        
        session.commit()
        print(f"✓ Super admin user '{super_admin_username}' promoted to super-admin!")
        return True
        
    except Exception as e:
        print(f"Error ensuring super admin: {str(e)}")
        if 'session' in locals():
            session.rollback()
        return False
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    print("Super Admin Promotion Check")
    print("=" * 30)
    
    success = ensure_super_admin()
    
    if success:
        print("Super admin check completed successfully!")
    else:
        print("Super admin check failed!")
    
    # Don't exit with error code as this might prevent container startup
    # Just log the result
    sys.exit(0)
