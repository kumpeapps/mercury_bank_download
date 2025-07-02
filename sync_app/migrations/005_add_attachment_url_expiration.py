"""
Add URL expiration tracking to transaction attachments.

This migration adds a url_expires_at column to track when Mercury Bank attachment URLs expire.
Mercury URLs typically expire after 12 hours, so this allows the system to show expired status
instead of trying to display expired images.
"""

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import logging

logger = logging.getLogger(__name__)

def upgrade(db_session):
    """Add url_expires_at column to transaction_attachments table."""
    try:
        # Check if column already exists
        result = db_session.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'transaction_attachments' 
            AND column_name = 'url_expires_at'
            AND table_schema = DATABASE()
        """))
        
        if result.scalar() == 0:
            # Add the column
            db_session.execute(text("""
                ALTER TABLE transaction_attachments 
                ADD COLUMN url_expires_at DATETIME DEFAULT NULL
            """))
            db_session.commit()
            logger.info("Added url_expires_at column to transaction_attachments table")
        else:
            logger.info("url_expires_at column already exists in transaction_attachments table")
            
    except OperationalError as e:
        logger.warning("Failed to add url_expires_at column: %s", e)
        db_session.rollback()

def downgrade(db_session):
    """Remove url_expires_at column from transaction_attachments table."""
    try:
        # Check if column exists before dropping
        result = db_session.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'transaction_attachments' 
            AND column_name = 'url_expires_at'
            AND table_schema = DATABASE()
        """))
        
        if result.scalar() > 0:
            # Drop the column
            db_session.execute(text("""
                ALTER TABLE transaction_attachments 
                DROP COLUMN url_expires_at
            """))
            db_session.commit()
            logger.info("Removed url_expires_at column from transaction_attachments table")
        else:
            logger.info("url_expires_at column does not exist in transaction_attachments table")
            
    except OperationalError as e:
        logger.warning("Failed to remove url_expires_at column: %s", e)
        db_session.rollback()
