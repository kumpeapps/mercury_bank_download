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


def ensure_first_user_is_admin():
    """Ensure the first user in the system has admin privileges."""
    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False

    try:
        # Create database engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        print("Checking user admin status...")

        # Check if any admin users exist
        admin_count = (
            session.query(User)
            .join(UserSettings)
            .filter(UserSettings.is_admin == True)
            .count()
        )

        if admin_count > 0:
            print(f"Found {admin_count} admin user(s). No action needed.")
            return True

        print("No admin users found. Looking for first user to promote...")

        # Get the first user (oldest by ID)
        first_user = session.query(User).order_by(User.id).first()

        if not first_user:
            print("No users found in the system.")
            return True

        print(f"Promoting first user '{first_user.username}' to admin...")

        # Check if user has settings
        if not first_user.settings:
            # Create settings with admin privileges
            user_settings = UserSettings(user_id=first_user.id, is_admin=True)
            session.add(user_settings)
        else:
            # Update existing settings
            first_user.settings.is_admin = True

        session.commit()
        print(f"✓ User '{first_user.username}' has been promoted to admin!")
        return True

    except Exception as e:
        print(f"Error ensuring admin user: {str(e)}")
        if "session" in locals():
            session.rollback()
        return False
    finally:
        if "session" in locals():
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
