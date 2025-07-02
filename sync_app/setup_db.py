#!/usr/bin/env python3
"""
Mercury Bank Database Setup Script

This script helps initialize the database with the new User and MercuryAccount models.
It also provides examples of how to create initial records for testing and production.

Features:
- Initialize database tables
- Create sample data for testing
- Interactive setup for production data
- Password hashing utilities
- Migration verification
"""

import os
import sys
import uuid
import getpass
from datetime import datetime
from sqlalchemy import text

from models import User, MercuryAccount, Account, Transaction, SystemSetting
from models.base import create_engine_and_session, init_db
from sqlalchemy.orm import Session
from sqlalchemy import text


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    try:
        import bcrypt

        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except ImportError:
        print("⚠️  Warning: bcrypt not available, using plain text (NOT SECURE)")
        return password  # For development only - not secure!


def setup_database():
    """Initialize the database with all tables."""
    print("Setting up database tables...")
    try:
        # Create tables
        init_db()
        print("✅ Database tables created successfully!")
        
        # Initialize system settings
        engine, SessionLocal = create_engine_and_session()
        db = SessionLocal()
        try:
            initialize_system_settings(db)
        finally:
            db.close()
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        raise


def verify_migration(db: Session) -> bool:
    """
    Verify that the database has been properly migrated.

    Args:
        db: Database session

    Returns:
        bool: True if migration is complete
    """
    try:
        # Try to query each table to verify they exist
        user_count = db.query(User).count()
        mercury_account_count = db.query(MercuryAccount).count()
        account_count = db.query(Account).count()

        print(f"✅ Migration verification successful:")
        print(f"   - Users: {user_count}")
        print(f"   - Mercury Accounts: {mercury_account_count}")
        print(f"   - Accounts: {account_count}")

        return True
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False


def create_production_mercury_account(db: Session) -> int:
    """
    Interactively create a production Mercury account.

    Args:
        db: Database session

    Returns:
        int: ID of the created Mercury account
    """
    print("\n📝 Creating Mercury Account Group")
    print("-" * 40)

    name = input("Account group name: ").strip()
    if not name:
        raise ValueError("Account name is required")

    api_key = getpass.getpass("Mercury API key: ").strip()
    if not api_key:
        raise ValueError("API key is required")

    sandbox_mode = input("Use sandbox mode? (y/N): ").lower().strip() == "y"
    description = input("Description (optional): ").strip() or None

    mercury_account = MercuryAccount(
        name=name,
        api_key=api_key,
        sandbox_mode=sandbox_mode,
        description=description,
        is_active=True,
        sync_enabled=True,
    )

    db.add(mercury_account)
    db.flush()
    mercury_account_id = mercury_account.id

    print(f"✅ Created Mercury account: {name} (ID: {mercury_account_id})")
    return int(mercury_account_id) if mercury_account_id else 0


def create_production_user(db: Session, mercury_account_id: int) -> int:
    """
    Interactively create a production user.

    Args:
        db: Database session
        mercury_account_id: ID of the Mercury account to associate with

    Returns:
        int: ID of the created user
    """
    print("\n👤 Creating User Account")
    print("-" * 40)

    username = input("Username: ").strip()
    if not username:
        raise ValueError("Username is required")

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise ValueError(f"Username '{username}' already exists")

    email = input("Email: ").strip()
    if not email:
        raise ValueError("Email is required")

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise ValueError(f"Email '{email}' already exists")

    password = getpass.getpass("Password: ").strip()
    if not password:
        raise ValueError("Password is required")

    password_confirm = getpass.getpass("Confirm password: ").strip()
    if password != password_confirm:
        raise ValueError("Passwords do not match")

    first_name = input("First name (optional): ").strip() or None
    last_name = input("Last name (optional): ").strip() or None
    is_admin = input("Admin user? (y/N): ").lower().strip() == "y"

    # Hash the password
    password_hash = hash_password(password)

    # Get the Mercury account to associate with
    mercury_account = (
        db.query(MercuryAccount).filter(MercuryAccount.id == mercury_account_id).first()
    )

    if not mercury_account:
        raise ValueError(f"Mercury account {mercury_account_id} not found")

    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        is_admin=is_admin,
    )

    # Associate user with Mercury account
    user.mercury_accounts.append(mercury_account)

    db.add(user)
    db.flush()
    user_id = user.id

    print(f"✅ Created user: {username} (ID: {user_id})")
    return int(user_id) if user_id else 0


def create_sample_mercury_account(db: Session) -> int:
    """
    Create a sample Mercury account group.

    Args:
        db: Database session

    Returns:
        int: ID of the created Mercury account
    """
    sample_mercury_account = MercuryAccount(
        name="Sample Company Mercury Account",
        api_key="your_mercury_api_key_here",  # Replace with actual API key
        sandbox_mode=True,  # Set to False for production
        description="Sample Mercury Bank account group for testing",
        is_active=True,
        sync_enabled=True,
    )

    db.add(sample_mercury_account)
    db.flush()  # Flush to get the auto-generated ID
    mercury_account_id = sample_mercury_account.id
    print(f"Created sample Mercury account: {mercury_account_id}")
    return int(mercury_account_id) if mercury_account_id else 0


def create_sample_user(db: Session, mercury_account_id: int) -> int:
    """
    Create a sample user and associate with the Mercury account.

    Args:
        db: Database session
        mercury_account_id: ID of the Mercury account to associate with

    Returns:
        int: ID of the created user
    """
    # Get the Mercury account to associate with
    mercury_account = (
        db.query(MercuryAccount).filter(MercuryAccount.id == mercury_account_id).first()
    )

    if not mercury_account:
        raise ValueError(f"Mercury account {mercury_account_id} not found")

    sample_user = User(
        username="admin",
        email="admin@company.com",
        password_hash="$2b$12$dummy_hash_replace_with_real_hash",  # Replace with real password hash
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_admin=True,
    )

    # Associate user with Mercury account
    sample_user.mercury_accounts.append(mercury_account)

    db.add(sample_user)
    db.flush()  # Flush to get the auto-generated ID
    user_id = sample_user.id
    print(f"Created sample user: {user_id}")
    return int(user_id) if user_id else 0


def initialize_system_settings(db: Session):
    """Initialize default system settings if they don't exist."""
    try:
        # Check if users table is a view to set default signup behavior
        try:
            result = db.execute(text(
                """
                SELECT TABLE_TYPE 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'users'
                """
            )).fetchone()

            default_signup_enabled = result[0] != "VIEW" if result else True
        except Exception:
            default_signup_enabled = True

        # Initialize default settings
        settings_to_create = [
            (
                "registration_enabled",
                str(default_signup_enabled),
                "Whether new user registration is enabled",
                True,
            ),
            (
                "prevent_user_deletion",
                "false",
                "Prevent administrators from deleting user accounts",
                True,
            ),
        ]

        for key, value, description, is_editable in settings_to_create:
            existing = db.query(SystemSetting).filter_by(key=key).first()
            if not existing:
                setting = SystemSetting(
                    key=key,
                    value=value,
                    description=description,
                    is_editable=is_editable,
                )
                db.add(setting)

        db.commit()
        print("✅ System settings initialized")
    except Exception as e:
        print(f"❌ Warning: Could not initialize system settings: {e}")
        db.rollback()


def main():
    """Main setup function."""
    print("🏦 Mercury Bank Database Setup")
    print("=" * 50)

    # Setup database
    setup_database()

    # Create database session
    engine, session_local = create_engine_and_session()
    db = session_local()

    try:
        # Verify migration
        if not verify_migration(db):
            print("❌ Database verification failed. Please run migration.sql first.")
            sys.exit(1)

        # Initialize system settings
        initialize_system_settings(db)

        print("\n🚀 Setup Options:")
        print("1. Create sample data for testing")
        print("2. Create production data interactively")
        print("3. Skip data creation")

        choice = input("\nChoose an option (1-3): ").strip()

        if choice == "1":
            print("\n📊 Creating sample data...")
            # Create sample Mercury account
            mercury_account_id = create_sample_mercury_account(db)

            # Create sample user
            user_id = create_sample_user(db, mercury_account_id)

            db.commit()
            print("\n✅ Sample data created successfully!")
            print(f"   Mercury Account ID: {mercury_account_id}")
            print(f"   User ID: {user_id}")

            print("\n⚠️  Next steps for sample data:")
            print("   1. Update the Mercury account with your actual API key")
            print("   2. Update the user with a proper password hash")
            print("   3. Run the sync script to start syncing data")

        elif choice == "2":
            print("\n🏭 Creating production data...")

            # Create production Mercury account
            mercury_account_id = create_production_mercury_account(db)

            # Create production user
            user_id = create_production_user(db, mercury_account_id)

            db.commit()
            print("\n✅ Production data created successfully!")
            print(f"   Mercury Account ID: {mercury_account_id}")
            print(f"   User ID: {user_id}")

            print("\n🎉 Next steps:")
            print("   1. Start the synchronization service")
            print("   2. Monitor logs for sync activity")
            print("   3. Set up additional users as needed")

        elif choice == "3":
            print("\n⏭️  Skipping data creation")
            print("   You can create data later using this script or manually")

        else:
            print("❌ Invalid choice. Exiting.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        db.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

    print("\n🎯 Database setup complete!")
    print("\n📚 Additional Resources:")
    print("   - Multi-Account Guide: MULTI_ACCOUNT_README.md")
    print("   - Docker Troubleshooting: DOCKER_TROUBLESHOOTING.md")
    print("   - Main Documentation: README.md")


if __name__ == "__main__":
    main()
