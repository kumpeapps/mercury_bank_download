#!/usr/bin/env python3
"""
Utility script to create the first admin user or promote an existing user to admin.

This script can be used to:
1. Create a new admin user if no users exist
2. Promote an existing user to admin status
3. Check admin status of users
"""

import os
import sys
import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.user import User
from models.user_settings import UserSettings
from models.base import Base


def create_first_admin():
    """Create the first admin user if no users exist."""
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
        
        print("Checking existing users...")
        
        # Check if any users exist
        user_count = session.query(User).count()
        
        if user_count > 0:
            print(f"Found {user_count} existing users.")
            print("To promote an existing user to admin, use the --promote option.")
            return False
        
        print("No users found. Creating first admin user...")
        
        # Get user input
        username = input("Enter username for admin user: ").strip()
        if not username:
            print("Username cannot be empty")
            return False
            
        email = input("Enter email for admin user: ").strip()
        if not email:
            print("Email cannot be empty")
            return False
            
        password = getpass.getpass("Enter password for admin user: ")
        if not password:
            print("Password cannot be empty")
            return False
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match")
            return False
        
        # Create the admin user
        admin_user = User(username=username, email=email)
        admin_user.set_password(password)
        session.add(admin_user)
        session.flush()  # Get the user ID
        
        # Create user settings with admin privileges
        user_settings = UserSettings(user_id=admin_user.id, is_admin=True)
        session.add(user_settings)
        session.commit()
        
        print(f"✓ Admin user '{username}' created successfully!")
        return True
        
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        if 'session' in locals():
            session.rollback()
        return False
    finally:
        if 'session' in locals():
            session.close()


def promote_user_to_admin(username):
    """Promote an existing user to admin status."""
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
        
        # Find the user
        user = session.query(User).filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found")
            return False
        
        # Check if user already has settings
        if not user.settings:
            user_settings = UserSettings(user_id=user.id, is_admin=True)
            session.add(user_settings)
        else:
            user.settings.is_admin = True
        
        session.commit()
        print(f"✓ User '{username}' has been promoted to admin!")
        return True
        
    except Exception as e:
        print(f"Error promoting user: {str(e)}")
        if 'session' in locals():
            session.rollback()
        return False
    finally:
        if 'session' in locals():
            session.close()


def list_admin_users():
    """List all admin users."""
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
        
        # Get all users with their settings
        users = session.query(User).join(UserSettings, User.id == UserSettings.user_id).all()
        
        admin_users = [user for user in users if user.is_admin]
        
        if admin_users:
            print(f"Found {len(admin_users)} admin user(s):")
            for user in admin_users:
                print(f"  - {user.username} ({user.email})")
        else:
            print("No admin users found")
        
        return True
        
    except Exception as e:
        print(f"Error listing users: {str(e)}")
        return False
    finally:
        if 'session' in locals():
            session.close()


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Admin User Management Utility")
        print("=" * 30)
        print("Usage:")
        print("  python admin_user.py create     - Create first admin user")
        print("  python admin_user.py promote <username> - Promote user to admin")  
        print("  python admin_user.py list       - List all admin users")
        return
    
    command = sys.argv[1].lower()
    
    if command == "create":
        create_first_admin()
    elif command == "promote":
        if len(sys.argv) < 3:
            print("Usage: python admin_user.py promote <username>")
            return
        username = sys.argv[2]
        promote_user_to_admin(username)
    elif command == "list":
        list_admin_users()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: create, promote, list")


if __name__ == "__main__":
    main()
