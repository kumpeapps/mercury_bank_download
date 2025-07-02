#!/usr/bin/env python3
"""
Web Application Database Setup Script

This script sets up the database for the Mercury Bank Web Interface.
It creates all necessary tables and can optionally create an admin user.
"""

import os
import sys
from getpass import getpass
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.user import User
from models.mercury_account import MercuryAccount
from models.account import Account
from models.transaction import Transaction

def setup_database():
    """Create all database tables."""
    DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://mercury_user:mercury_password@localhost:3306/mercury_bank')
    
    print("Setting up Mercury Bank Web Interface database...")
    print(f"Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Local'}")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(engine)
        print("✓ Database tables created successfully!")
        
        return engine
    except Exception as e:
        print(f"✗ Error creating database tables: {e}")
        return None

def create_admin_user(engine):
    """Create an admin user for the web interface."""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("\nCreating admin user...")
        
        # Check if any users exist
        existing_users = session.query(User).count()
        if existing_users > 0:
            print("Users already exist in the database.")
            create_new = input("Do you want to create another admin user? (y/N): ").lower()
            if create_new != 'y':
                return
        
        # Get user details
        username = input("Enter admin username: ").strip()
        if not username:
            print("Username cannot be empty!")
            return
        
        # Check if username exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists!")
            return
        
        email = input("Enter admin email: ").strip()
        if not email:
            print("Email cannot be empty!")
            return
        
        # Check if email exists
        existing_email = session.query(User).filter_by(email=email).first()
        if existing_email:
            print(f"Email '{email}' already exists!")
            return
        
        password = getpass("Enter admin password: ")
        if not password:
            print("Password cannot be empty!")
            return
        
        password_confirm = getpass("Confirm admin password: ")
        if password != password_confirm:
            print("Passwords do not match!")
            return
        
        # Get optional profile information
        first_name = input("Enter first name (optional): ").strip() or None
        last_name = input("Enter last name (optional): ").strip() or None
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        admin_user.set_password(password)
        
        session.add(admin_user)
        session.flush()  # Flush to get the user ID
        
        # Create user settings with admin privileges
        from models.user_settings import UserSettings
        admin_settings = UserSettings(
            user_id=admin_user.id,
            is_admin=True
        )
        session.add(admin_settings)
        session.commit()
        
        print(f"✓ Admin user '{username}' created successfully!")
        print(f"  Email: {email}")
        print(f"  Name: {admin_user.full_name}")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error creating admin user: {e}")
    finally:
        session.close()

def fix_invalid_password_hashes(engine):
    """Fix users with invalid password hashes."""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("\nChecking for users with invalid password hashes...")
        
        users = session.query(User).all()
        fixed_count = 0
        
        for user in users:
            if not user.has_valid_password():
                print(f"Found user '{user.username}' with invalid password hash.")
                
                # Option 1: Reset password to a default
                reset_option = input(f"Reset password for '{user.username}'? (y/N): ").lower()
                if reset_option == 'y':
                    new_password = getpass(f"Enter new password for '{user.username}': ")
                    if new_password:
                        user.set_password(new_password)
                        fixed_count += 1
                        print(f"✓ Password reset for '{user.username}'")
                    else:
                        print(f"✗ Skipped '{user.username}' - empty password")
                else:
                    print(f"✗ Skipped '{user.username}'")
        
        if fixed_count > 0:
            session.commit()
            print(f"\n✓ Fixed {fixed_count} user(s) with invalid password hashes")
        else:
            print("✓ No users with invalid password hashes found")
            
    except Exception as e:
        session.rollback()
        print(f"✗ Error fixing password hashes: {e}")
    finally:
        session.close()

def main():
    """Main setup function."""
    print("=" * 60)
    print("Mercury Bank Web Interface - Database Setup")
    print("=" * 60)
    
    # Setup database
    engine = setup_database()
    if not engine:
        sys.exit(1)
    
    # Fix invalid password hashes
    fix_hashes = input("\nDo you want to check/fix invalid password hashes? (Y/n): ").lower()
    if fix_hashes != 'n':
        fix_invalid_password_hashes(engine)
    
    # Create admin user
    create_admin = input("\nDo you want to create an admin user? (Y/n): ").lower()
    if create_admin != 'n':
        create_admin_user(engine)
    
    # Fix invalid password hashes
    fix_hashes = input("\nDo you want to fix users with invalid password hashes? (Y/n): ").lower()
    if fix_hashes != 'n':
        fix_invalid_password_hashes(engine)
    
    print("\n" + "=" * 60)
    print("Setup completed!")
    print("\nYou can now start the web application with:")
    print("  cd web_app")
    print("  docker-compose up")
    print("\nOr run locally with:")
    print("  cd web_app")
    print("  python app.py")
    print("\nThe web interface will be available at:")
    print("  http://localhost:5000")
    print("=" * 60)

if __name__ == "__main__":
    main()
