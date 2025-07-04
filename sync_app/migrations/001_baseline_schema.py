"""
Baseline migration - establish current schema using SQLAlchemy

This migration creates all the current tables using SQLAlchemy models,
providing a clean starting point for future migrations.
"""

from models.base import Base


def upgrade(engine):
    """Create all tables using SQLAlchemy models in the correct order"""
    # Import all models to ensure they're registered with Base.metadata
    from models.user import User
    from models.role import Role
    from models.user_settings import UserSettings  
    from models.mercury_account import MercuryAccount
    from models.account import Account
    from models.transaction import Transaction
    from models.transaction_attachment import TransactionAttachment
    from models.system_setting import SystemSetting
    
    # Create tables in the correct order to satisfy foreign key constraints
    
    # First create tables without foreign key dependencies
    User.__table__.create(bind=engine, checkfirst=True)
    Role.__table__.create(bind=engine, checkfirst=True)
    MercuryAccount.__table__.create(bind=engine, checkfirst=True)
    SystemSetting.__table__.create(bind=engine, checkfirst=True)
    
    # Create the user-role association table
    from models.base import user_role_association
    user_role_association.create(bind=engine, checkfirst=True)
    
    # Create Account table before UserSettings (since UserSettings references accounts.id)
    Account.__table__.create(bind=engine, checkfirst=True)
    
    # Now create UserSettings (depends on User and Account)
    UserSettings.__table__.create(bind=engine, checkfirst=True)
    
    # Create the association table
    from models.base import user_mercury_account_association
    user_mercury_account_association.create(bind=engine, checkfirst=True)
    
    # Finally create Transaction table (depends on Account)
    Transaction.__table__.create(bind=engine, checkfirst=True)
    
    # Create TransactionAttachment table (depends on Transaction)
    TransactionAttachment.__table__.create(bind=engine, checkfirst=True)
    
    # Create the user account access table
    from models.base import user_account_access
    user_account_access.create(bind=engine, checkfirst=True)


def downgrade(engine):
    """Drop all tables in reverse order using SQLAlchemy"""
    # Import all models
    from models.user import User
    from models.user_settings import UserSettings
    from models.mercury_account import MercuryAccount
    from models.account import Account
    from models.transaction import Transaction
    from models.system_setting import SystemSetting
    from models.base import user_mercury_account_association, user_account_access
    
    # Drop tables in reverse order (respecting foreign key dependencies)
    # Drop tables with foreign key dependencies first
    Transaction.__table__.drop(bind=engine, checkfirst=True)
    Account.__table__.drop(bind=engine, checkfirst=True)
    user_account_access.drop(bind=engine, checkfirst=True)
    user_mercury_account_association.drop(bind=engine, checkfirst=True)
    UserSettings.__table__.drop(bind=engine, checkfirst=True)
    
    # Then drop tables without dependencies
    SystemSetting.__table__.drop(bind=engine, checkfirst=True)
    MercuryAccount.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)
