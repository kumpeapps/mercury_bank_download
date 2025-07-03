"""
Migration 008: Add exclude_from_reports column to accounts table

This migration adds a boolean column 'exclude_from_reports' to the accounts table
to allow users to exclude specific accounts from showing in reports and "all accounts" filters.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models.base import create_engine_and_session
import logging

logger = logging.getLogger(__name__)


def upgrade(db_session=None):
    """Add exclude_from_reports column to accounts table"""
    try:
        engine, SessionLocal = create_engine_and_session()
        session = SessionLocal()
        
        # Check if column already exists to make migration idempotent
        result = session.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'accounts' 
            AND COLUMN_NAME = 'exclude_from_reports'
        """))
        
        column_exists = result.fetchone()[0] > 0
        
        if not column_exists:
            print("Adding exclude_from_reports column to accounts table...")
            session.execute(text("""
                ALTER TABLE accounts 
                ADD COLUMN exclude_from_reports BOOLEAN DEFAULT FALSE NOT NULL
            """))
            session.commit()
            print("Successfully added exclude_from_reports column")
        else:
            print("exclude_from_reports column already exists, skipping...")
        
        session.close()
        return True
            
    except Exception as e:
        print(f"Error in migration 008 upgrade: {e}")
        logger.error(f"Error in migration 008 upgrade: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


def downgrade(db_session=None):
    """Remove exclude_from_reports column from accounts table"""
    try:
        engine, SessionLocal = create_engine_and_session()
        session = SessionLocal()
        
        # Check if column exists before dropping
        result = session.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'accounts' 
            AND COLUMN_NAME = 'exclude_from_reports'
        """))
        
        column_exists = result.fetchone()[0] > 0
        
        if column_exists:
            print("Removing exclude_from_reports column from accounts table...")
            session.execute(text("""
                ALTER TABLE accounts 
                DROP COLUMN exclude_from_reports
            """))
            session.commit()
            print("Successfully removed exclude_from_reports column")
        else:
            print("exclude_from_reports column does not exist, skipping...")
        
        session.close()
        return True
            
    except Exception as e:
        print(f"Error in migration 008 downgrade: {e}")
        logger.error(f"Error in migration 008 downgrade: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False
