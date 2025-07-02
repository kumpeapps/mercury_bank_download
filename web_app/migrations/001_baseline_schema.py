"""
Baseline migration - establish current schema using SQLAlchemy

This migration creates all the current tables using SQLAlchemy models,
providing a clean starting point for future migrations.
"""

from models.base import Base


def upgrade(engine):
    """Create all tables using SQLAlchemy models"""
    # Import all models to ensure they're registered with Base.metadata
    from models.user import User
    from models.user_settings import UserSettings  
    from models.mercury_account import MercuryAccount
    from models.account import Account
    from models.transaction import Transaction
    from models.system_setting import SystemSetting
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def downgrade(engine):
    """Drop all tables"""
    # Import all models
    from models.user import User
    from models.user_settings import UserSettings
    from models.mercury_account import MercuryAccount
    from models.account import Account
    from models.transaction import Transaction
    from models.system_setting import SystemSetting
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
