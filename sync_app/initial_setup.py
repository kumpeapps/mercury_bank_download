#!/usr/bin/env python3
"""
Initial Database Setup for Mercury Bank Integration Platform

This script creates all database tables and initial data for the first production release.
It replaces the complex migration system with a simple SQLAlchemy create_all() approach.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from datetime import datetime

# Add the app directory to the path so we can import models
sys.path.insert(0, "/app")

from models.base import Base, get_database_url
from models.user import User
from models.role import Role
from models.user_settings import UserSettings
from models.mercury_account import MercuryAccount
from models.account import Account
from models.transaction import Transaction
from models.transaction_attachment import TransactionAttachment
from models.system_setting import SystemSetting

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_database(engine, max_retries=30, retry_delay=2):
    """Wait for database to be available"""
    import time

    for attempt in range(max_retries):
        try:
            # Test database connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.info(
                    f"⏳ Database not ready (attempt {attempt + 1}/{max_retries}), waiting {retry_delay}s..."
                )
                time.sleep(retry_delay)
            else:
                logger.error(
                    f"❌ Database connection failed after {max_retries} attempts: {e}"
                )
                return False
    return False


def create_initial_roles(engine):
    """Create initial system roles"""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Define initial roles
        initial_roles = [
            {
                "name": "user",
                "description": "Standard user with basic access to their own data",
                "is_system_role": True,
            },
            {
                "name": "admin",
                "description": "Administrator with full system access",
                "is_system_role": True,
            },
            {
                "name": "super-admin",
                "description": "Super administrator with complete system control",
                "is_system_role": True,
            },
            {
                "name": "reports",
                "description": "User with access to reporting features",
                "is_system_role": True,
            },
        ]

        for role_data in initial_roles:
            # Check if role already exists
            existing_role = (
                session.query(Role).filter(Role.name == role_data["name"]).first()
            )
            if not existing_role:
                role = Role(**role_data)
                session.add(role)
                logger.info(f"✅ Created role: {role_data['name']}")
            else:
                logger.info(f"ℹ️  Role already exists: {role_data['name']}")

        session.commit()
        logger.info("✅ Initial roles created successfully")

    except Exception as e:
        logger.error(f"❌ Error creating initial roles: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def create_initial_system_settings(engine):
    """Create initial system settings"""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Define initial system settings
        initial_settings = [
            {
                "key": "registration_enabled",
                "value": "true",
                "description": "Allow new user registration",
            },
            {
                "key": "users_externally_managed",
                "value": os.getenv("USERS_EXTERNALLY_MANAGED", "false").lower(),
                "description": "Whether users are managed by external system",
            },
            {
                "key": "app_name",
                "value": "Mercury Bank Integration Platform",
                "description": "Application name displayed in the interface",
            },
            {
                "key": "app_description",
                "value": "Mercury Bank data synchronization and management platform",
                "description": "Application description",
            },
            {"key": "logo_url", "value": "", "description": "URL to application logo"},
        ]

        for setting_data in initial_settings:
            # Check if setting already exists
            existing_setting = (
                session.query(SystemSetting)
                .filter(SystemSetting.key == setting_data["key"])
                .first()
            )
            if not existing_setting:
                setting = SystemSetting(**setting_data)
                session.add(setting)
                logger.info(
                    f"✅ Created system setting: {setting_data['key']} = {setting_data['value']}"
                )
            else:
                logger.info(f"ℹ️  System setting already exists: {setting_data['key']}")

        session.commit()
        logger.info("✅ Initial system settings created successfully")

    except Exception as e:
        logger.error(f"❌ Error creating initial system settings: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Main setup function"""
    logger.info("🚀 Starting Mercury Bank Integration Platform Initial Setup...")

    # Get database URL
    database_url = get_database_url()
    logger.info(
        f"🔧 Using database: {database_url.split('@')[-1] if '@' in database_url else 'local'}"
    )

    # Create engine
    engine = create_engine(database_url, echo=False)

    # Wait for database to be ready
    logger.info("⏳ Waiting for database to be ready...")
    if not wait_for_database(engine):
        logger.error("❌ Database setup failed - could not connect")
        sys.exit(1)

    try:
        # Create all tables using SQLAlchemy
        logger.info("🔄 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")

        # Create initial roles
        logger.info("🔄 Creating initial roles...")
        create_initial_roles(engine)

        # Create initial system settings
        logger.info("🔄 Creating initial system settings...")
        create_initial_system_settings(engine)

        logger.info(
            "✅ Mercury Bank Integration Platform initial setup completed successfully!"
        )

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
