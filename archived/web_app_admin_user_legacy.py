#!/usr/bin/env python3
"""
Utility script to create the first admin user or promote an existing user to admin.

This script can be used to:
1. Create a new admin user if no users exist
2. Promote an existing user to admin status
3. Demote an admin user to regular user
4. Add a new user
5. Delete an existing user
6. List all users
7. Toggle user registration on/off
8. List admin users
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
from models.system_setting import SystemSetting
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


def demote_admin_user(username):
    """Remove admin privileges from a user."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Find the user
        user = session.query(User).filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found")
            return False
        
        # Check if user is an admin
        if not user.is_admin:
            print(f"User '{username}' is not an admin")
            return True
        
        # Remove admin privileges
        if user.settings:
            user.settings.is_admin = False
            session.commit()
            print(f"✓ Admin privileges removed from user '{username}'")
            return True
        else:
            print(f"User '{username}' has no settings record")
            return False
        
    except Exception as e:
        print(f"Error demoting admin: {str(e)}")
        if 'session' in locals():
            session.rollback()
        return False
    finally:
        if 'session' in locals():
            session.close()


def add_user():
    """Add a new user to the system."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Creating a new user account...")
        
        # Get user input
        username = input("Enter username: ").strip()
        if not username:
            print("Username cannot be empty")
            return False
        
        # Check if username already exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            print(f"Error: Username '{username}' already exists")
            return False
            
        email = input("Enter email: ").strip()
        if not email:
            print("Email cannot be empty")
            return False
        
        # Check if email already exists
        existing_email = session.query(User).filter_by(email=email).first()
        if existing_email:
            print(f"Error: Email '{email}' already exists")
            return False
            
        password = getpass.getpass("Enter password: ")
        if not password:
            print("Password cannot be empty")
            return False
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match")
            return False
        
        is_admin = input("Should this user be an admin? (y/n): ").strip().lower() == 'y'
        
        # Create the user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        session.add(new_user)
        session.flush()  # Get the user ID
        
        # Create user settings
        user_settings = UserSettings(user_id=new_user.id, is_admin=is_admin)
        session.add(user_settings)
        session.commit()
        
        print(f"✓ User '{username}' created successfully!")
        if is_admin:
            print("  - User has admin privileges")
        return True
        
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        if 'session' in locals():
            session.rollback()
        return False
    finally:
        if 'session' in locals():
            session.close()


def delete_user(username):
    """Delete a user from the system."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if user deletion is prevented by system settings
        from models.system_setting import SystemSetting
        if SystemSetting.get_bool_value(session, "prevent_user_deletion", default=False):
            print("User deletion is disabled by system settings.")
            return False
        
        # Find the user
        user = session.query(User).filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found")
            return False
        
        # Confirm deletion
        confirm = input(f"Are you sure you want to delete user '{username}'? This cannot be undone. (y/n): ").strip().lower()
        if confirm != 'y':
            print("User deletion cancelled")
            return False
        
        # Delete the user
        session.delete(user)
        session.commit()
        print(f"✓ User '{username}' deleted successfully")
        return True
        
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        if 'session' in locals():
            session.rollback()
        return False
    finally:
        if 'session' in locals():
            session.close()


def list_users():
    """List all users in the system."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get all users
        users = session.query(User).all()
        
        if users:
            print(f"Found {len(users)} user(s):")
            print("| Username              | Email                           | Admin |")
            print("|----------------------|--------------------------------|-------|")
            for user in users:
                admin_status = "Yes" if user.is_admin else "No"
                print(f"| {user.username:<20} | {user.email:<30} | {admin_status:<5} |")
        else:
            print("No users found")
        
        return True
        
    except Exception as e:
        print(f"Error listing users: {str(e)}")
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


def toggle_signup():
    """Toggle user registration on/off."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check current setting
        setting_key = "registration_enabled"
        current_setting = SystemSetting.get_bool_value(session, setting_key, default=True)
        
        # Toggle the setting
        new_setting = not current_setting
        SystemSetting.set_value(
            session, 
            setting_key, 
            "true" if new_setting else "false",
            description="Whether user registration is enabled",
            is_editable=True
        )
        
        if new_setting:
            print("✓ User registration has been ENABLED")
        else:
            print("✓ User registration has been DISABLED")
        
        return True
        
    except Exception as e:
        print(f"Error toggling signup: {str(e)}")
        if 'session' in locals():
            session.rollback()
        return False
    finally:
        if 'session' in locals():
            session.close()


def toggle_user_deletion_prevention():
    """Toggle whether user deletion is prevented."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check current setting
        setting_key = "prevent_user_deletion"
        current_setting = SystemSetting.get_bool_value(session, setting_key, default=False)
        
        # Toggle the setting
        new_setting = not current_setting
        SystemSetting.set_value(
            session, 
            setting_key, 
            "true" if new_setting else "false",
            description="Prevent administrators from deleting user accounts",
            is_editable=True
        )
        
        if new_setting:
            print("✓ User deletion prevention has been ENABLED")
            print("  Administrators can no longer delete user accounts")
        else:
            print("✓ User deletion prevention has been DISABLED")
            print("  Administrators can now delete user accounts")
        
        return True
        
    except Exception as e:
        print(f"Error toggling user deletion prevention: {str(e)}")
        if 'session' in locals():
            session.rollback()
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
        print("  python admin_user.py demote <username>  - Demote admin to user")
        print("  python admin_user.py add        - Add a new user")
        print("  python admin_user.py delete <username> - Delete a user")
        print("  python admin_user.py list       - List all users")
        print("  python admin_user.py toggle_signup - Toggle user registration")
        print("  python admin_user.py list_admin - List all admin users")
        print("  python admin_user.py toggle_user_deletion - Toggle user deletion prevention")
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
    elif command == "demote":
        if len(sys.argv) < 3:
            print("Usage: python admin_user.py demote <username>")
            return
        username = sys.argv[2]
        demote_admin_user(username)
    elif command == "add":
        add_user()
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: python admin_user.py delete <username>")
            return
        username = sys.argv[2]
        delete_user(username)
    elif command == "list":
        list_users()
    elif command == "toggle_signup":
        toggle_signup()
    elif command == "list_admin":
        list_admin_users()
    elif command == "toggle_user_deletion":
        toggle_user_deletion_prevention()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: create, promote, demote, add, delete, list, toggle_signup, list_admin, toggle_user_deletion")


if __name__ == "__main__":
    main()
