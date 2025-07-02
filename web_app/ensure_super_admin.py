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
        
        # Check if user already has admin privileges
        if user.is_admin:
            print(f"✓ Super admin user '{super_admin_username}' already has admin privileges")
            return True
        
        print(f"Promoting user '{super_admin_username}' to admin...")
        
        # Ensure user has settings
        if not user.settings:
            user_settings = UserSettings(user_id=user.id, is_admin=True)
            session.add(user_settings)
        else:
            user.settings.is_admin = True
        
        session.commit()
        print(f"✓ Super admin user '{super_admin_username}' promoted to admin!")
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
