#!/usr/bin/env python3
"""
Utility script to manage users and roles in the system.

This script can be used to:
1. Create a new admin/super-admin user if no users exist
2. Assign or remove roles from users
3. Add a new user with specific roles
4. Delete an existing user
5. List all users and their roles
6. Toggle user registration on/off
7. Toggle user deletion prevention
8. List users with specific roles
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
from models.role import Role


def create_first_admin(super_admin=False):
    """Create a new admin user if no users exist."""
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
        
        # Check if any users exist
        if session.query(User).count() > 0:
            print("Users already exist in the database.")
            print("To promote a user to admin, use: ./dev.sh assign-role <username> admin")
            print("To promote a user to super-admin, use: ./dev.sh assign-role <username> super-admin")
            return False
        
        # Prompt for user details
        print("Creating first admin user...")
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("Passwords do not match")
            return False
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        session.add(user)
        session.flush()  # Flush to get the user ID
        
        # Create user settings (for backward compatibility)
        user_settings = UserSettings(user_id=user.id, is_admin=True)
        session.add(user_settings)
        
        # Add roles
        role_name = "super-admin" if super_admin else "admin"
        role = session.query(Role).filter_by(name=role_name).first()
        if not role:
            print(f"Role '{role_name}' not found, creating it...")
            role = Role(name=role_name, 
                       description=f"{'Super administrator with full access' if super_admin else 'Administrator with management rights'}",
                       is_system_role=True)
            session.add(role)
            session.flush()
        
        # Also add the 'user' role for basic access
        user_role = session.query(Role).filter_by(name="user").first()
        if not user_role:
            user_role = Role(name="user", 
                           description="Regular user with basic access",
                           is_system_role=True)
            session.add(user_role)
            session.flush()
        
        # Assign roles to user
        user.roles.append(role)
        user.roles.append(user_role)
        
        session.commit()
        print(f"✓ First {role_name} user '{username}' created successfully!")
        return True
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False


def assign_role(username, role_name):
    """Assign a role to a user."""
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
        
        # Find the role
        role = session.query(Role).filter_by(name=role_name).first()
        if not role:
            print(f"Role '{role_name}' not found")
            choice = input("Would you like to create this role? (y/n): ").strip().lower()
            if choice != 'y':
                return False
            
            description = input(f"Description for '{role_name}' role: ").strip()
            role = Role(name=role_name, description=description, is_system_role=False)
            session.add(role)
            session.flush()
        
        # Check if user already has this role
        if user.has_role(role_name):
            print(f"User '{username}' already has the '{role_name}' role")
            return True
        
        # Assign role to user
        user.roles.append(role)
        
        # For backward compatibility with is_admin flag
        if role_name in ['admin', 'super-admin'] and user.settings:
            user.settings.is_admin = True
        
        session.commit()
        print(f"✓ Role '{role_name}' assigned to user '{username}' successfully!")
        return True
        
    except Exception as e:
        print(f"Error assigning role: {e}")
        return False


def remove_role(username, role_name):
    """Remove a role from a user."""
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
        
        # Find the role
        role = session.query(Role).filter_by(name=role_name).first()
        if not role:
            print(f"Role '{role_name}' not found")
            return False
        
        # Check if user has this role
        if not user.has_role(role_name):
            print(f"User '{username}' does not have the '{role_name}' role")
            return True
        
        # Remove role from user
        user.roles.remove(role)
        
        # For backward compatibility with is_admin flag
        if role_name in ['admin', 'super-admin'] and user.settings:
            # Only remove is_admin if they don't have any other admin roles
            if not user.has_role('admin') and not user.has_role('super-admin'):
                user.settings.is_admin = False
        
        session.commit()
        print(f"✓ Role '{role_name}' removed from user '{username}' successfully!")
        return True
        
    except Exception as e:
        print(f"Error removing role: {e}")
        return False


def add_user(role_names=None):
    """Add a new user with specified roles."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if user signup is allowed
        setting = session.query(SystemSetting).filter_by(key='user_signup_enabled').first()
        signup_enabled = setting and setting.value.lower() == 'true'
        
        # Prompt for user details
        print("Adding new user...")
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("Passwords do not match")
            return False
        
        # Check if user already exists
        if session.query(User).filter_by(username=username).first():
            print(f"User '{username}' already exists")
            return False
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        session.add(user)
        session.flush()  # Flush to get the user ID
        
        # Create user settings
        user_settings = UserSettings(user_id=user.id, is_admin=False)
        session.add(user_settings)
        
        # Assign roles
        if role_names:
            role_list = [r.strip() for r in role_names.split(',')]
        else:
            print("Available roles:")
            for role in session.query(Role).all():
                print(f"- {role.name}: {role.description}")
            role_input = input("Assign roles (comma-separated, leave blank for 'user' only): ").strip()
            role_list = [r.strip() for r in role_input.split(',')] if role_input else ['user']
        
        for role_name in role_list:
            if not role_name:  # Skip empty role names
                continue
                
            # Find or create the role
            role = session.query(Role).filter_by(name=role_name).first()
            if not role:
                print(f"Role '{role_name}' not found, creating it...")
                description = input(f"Description for '{role_name}' role: ").strip()
                role = Role(name=role_name, description=description, is_system_role=False)
                session.add(role)
                session.flush()
            
            # Assign role to user
            user.roles.append(role)
            
            # For backward compatibility with is_admin flag
            if role_name in ['admin', 'super-admin']:
                user_settings.is_admin = True
        
        session.commit()
        print(f"✓ User '{username}' created successfully with roles: {', '.join(role_list)}")
        return True
        
    except Exception as e:
        print(f"Error adding user: {e}")
        return False


def delete_user(username):
    """Delete an existing user."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if user deletion prevention is enabled
        setting = session.query(SystemSetting).filter_by(key='prevent_user_deletion').first()
        prevent_deletion = setting and setting.value.lower() == 'true'
        
        if prevent_deletion:
            print("User deletion is currently disabled in system settings.")
            print("To enable it, use: ./dev.sh toggle-user-deletion")
            return False
        
        # Find the user
        user = session.query(User).filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found")
            return False
        
        # Get confirmation
        confirm = input(f"Are you sure you want to delete user '{username}'? This cannot be undone. (y/n): ").strip().lower()
        if confirm != 'y':
            print("User deletion cancelled")
            return False
        
        # Delete user
        session.delete(user)
        session.commit()
        print(f"✓ User '{username}' deleted successfully!")
        return True
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False


def list_users():
    """List all users with their roles."""
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
        
        if not users:
            print("No users found in the database.")
            return True
        
        print("\nUser List:")
        print("=" * 80)
        print(f"{'Username':<20} {'Email':<30} {'Roles':<30}")
        print("-" * 80)
        
        for user in users:
            roles = ", ".join([role.name for role in user.roles]) or "none"
            print(f"{user.username:<20} {user.email:<30} {roles:<30}")
        
        print("=" * 80)
        print(f"Total: {len(users)} users")
        return True
        
    except Exception as e:
        print(f"Error listing users: {e}")
        return False


def list_users_by_role(role_name):
    """List all users with a specific role."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Find the role
        role = session.query(Role).filter_by(name=role_name).first()
        if not role:
            print(f"Role '{role_name}' not found")
            return False
        
        # Get all users with this role
        users_with_role = []
        for user in session.query(User).all():
            if user.has_role(role_name):
                users_with_role.append(user)
        
        if not users_with_role:
            print(f"No users found with the '{role_name}' role.")
            return True
        
        print(f"\nUsers with '{role_name}' role:")
        print("=" * 80)
        print(f"{'Username':<20} {'Email':<30} {'All Roles':<30}")
        print("-" * 80)
        
        for user in users_with_role:
            roles = ", ".join([r.name for r in user.roles])
            print(f"{user.username:<20} {user.email:<30} {roles:<30}")
        
        print("=" * 80)
        print(f"Total: {len(users_with_role)} users with '{role_name}' role")
        return True
        
    except Exception as e:
        print(f"Error listing users by role: {e}")
        return False


def list_roles():
    """List all available roles."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get all roles
        roles = session.query(Role).all()
        
        if not roles:
            print("No roles found in the database.")
            return True
        
        print("\nAvailable Roles:")
        print("=" * 80)
        print(f"{'Name':<20} {'System Role':<15} {'Description':<45}")
        print("-" * 80)
        
        for role in roles:
            system_role = "Yes" if role.is_system_role else "No"
            description = role.description or ""
            print(f"{role.name:<20} {system_role:<15} {description:<45}")
        
        print("=" * 80)
        print(f"Total: {len(roles)} roles")
        return True
        
    except Exception as e:
        print(f"Error listing roles: {e}")
        return False


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
        setting = session.query(SystemSetting).filter_by(key='user_signup_enabled').first()
        
        if not setting:
            # Create the setting if it doesn't exist
            setting = SystemSetting(key='user_signup_enabled', value='false')
            session.add(setting)
            current_value = 'false'
        else:
            current_value = setting.value
        
        # Toggle the value
        new_value = 'false' if current_value.lower() == 'true' else 'true'
        setting.value = new_value
        
        session.commit()
        print(f"✓ User registration {'enabled' if new_value == 'true' else 'disabled'} successfully!")
        return True
        
    except Exception as e:
        print(f"Error toggling signup: {e}")
        return False


def toggle_user_deletion_prevention():
    """Toggle user deletion prevention."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check current setting
        setting = session.query(SystemSetting).filter_by(key='prevent_user_deletion').first()
        
        if not setting:
            # Create the setting if it doesn't exist
            setting = SystemSetting(key='prevent_user_deletion', value='false')
            session.add(setting)
            current_value = 'false'
        else:
            current_value = setting.value
        
        # Toggle the value
        new_value = 'false' if current_value.lower() == 'true' else 'true'
        setting.value = new_value
        
        session.commit()
        print(f"✓ User deletion prevention {'enabled' if new_value == 'true' else 'disabled'} successfully!")
        return True
        
    except Exception as e:
        print(f"Error toggling user deletion prevention: {e}")
        return False


def create_role():
    """Create a new role."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Prompt for role details
        print("Creating new role...")
        name = input("Role name: ").strip()
        description = input("Description: ").strip()
        is_system_role_input = input("Is system role? (y/n): ").strip().lower()
        is_system_role = is_system_role_input == 'y'
        
        # Check if role already exists
        if session.query(Role).filter_by(name=name).first():
            print(f"Role '{name}' already exists")
            return False
        
        # Create role
        role = Role(name=name, description=description, is_system_role=is_system_role)
        session.add(role)
        session.commit()
        print(f"✓ Role '{name}' created successfully!")
        return True
        
    except Exception as e:
        print(f"Error creating role: {e}")
        return False


def main():
    """Main function to process command-line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python admin_user.py <command> [<args>]")
        print("\nCommands:")
        print("  create - Create first admin user")
        print("  create_super_admin - Create first super-admin user")
        print("  assign_role <username> <role> - Assign a role to a user")
        print("  remove_role <username> <role> - Remove a role from a user")
        print("  add - Add a new user")
        print("  add_with_roles <username> <roles> - Add a new user with specified roles")
        print("  delete <username> - Delete an existing user")
        print("  list - List all users")
        print("  list_by_role <role> - List users with a specific role")
        print("  list_roles - List all available roles")
        print("  create_role - Create a new role")
        print("  toggle_signup - Toggle user registration on/off")
        print("  toggle_user_deletion - Toggle user deletion prevention")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        create_first_admin()
    elif command == "create_super_admin":
        create_first_admin(super_admin=True)
    elif command == "assign_role":
        if len(sys.argv) < 4:
            print("Usage: python admin_user.py assign_role <username> <role>")
            return
        assign_role(sys.argv[2], sys.argv[3])
    elif command == "remove_role":
        if len(sys.argv) < 4:
            print("Usage: python admin_user.py remove_role <username> <role>")
            return
        remove_role(sys.argv[2], sys.argv[3])
    elif command == "add":
        add_user()
    elif command == "add_with_roles":
        if len(sys.argv) < 4:
            print("Usage: python admin_user.py add_with_roles <username> <roles>")
            return
        add_user(sys.argv[3])
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: python admin_user.py delete <username>")
            return
        delete_user(sys.argv[2])
    elif command == "list":
        list_users()
    elif command == "list_by_role":
        if len(sys.argv) < 3:
            print("Usage: python admin_user.py list_by_role <role>")
            return
        list_users_by_role(sys.argv[2])
    elif command == "list_roles":
        list_roles()
    elif command == "create_role":
        create_role()
    elif command == "toggle_signup":
        toggle_signup()
    elif command == "toggle_user_deletion":
        toggle_user_deletion_prevention()
    else:
        print(f"Unknown command: {command}")
        print("Run 'python admin_user.py' without arguments to see available commands")


if __name__ == "__main__":
    main()
