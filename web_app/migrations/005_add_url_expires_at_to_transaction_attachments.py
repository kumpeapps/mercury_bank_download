"""
Add url_expires_at column to transaction_attachments table.

This migration adds the url_expires_at column to track when Mercury Bank
attachment URLs expire (typically 12 hours after sync).
"""

from sqlalchemy import text
from models.base import create_engine_and_session
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade(engine=None):
    """Add url_expires_at column to transaction_attachments table."""
    logger.info("Adding url_expires_at column to transaction_attachments table...")
    
    if engine:
        # Use provided engine for connection
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        db_session = Session()
    else:
        _, db_session = create_engine_and_session()
    
    try:
        # Check if column already exists
        result = db_session.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'transaction_attachments'
            AND column_name = 'url_expires_at'
        """))
        
        column_exists = result.fetchone()[0] > 0
        
        if column_exists:
            logger.info("Column url_expires_at already exists, skipping addition")
            return
        
        # Add url_expires_at column
        db_session.execute(text("""
            ALTER TABLE transaction_attachments 
            ADD COLUMN url_expires_at DATETIME NULL
        """))
        
        # Add index for performance
        db_session.execute(text("""
            CREATE INDEX idx_transaction_attachments_url_expires_at 
            ON transaction_attachments(url_expires_at)
        """))
        
        db_session.commit()
        logger.info("Successfully added url_expires_at column to transaction_attachments table")
        
    except Exception as e:
        db_session.rollback()
        logger.error("Error adding url_expires_at column to transaction_attachments table: %s", e)
        raise
    finally:
        db_session.close()

def downgrade(engine=None):
    """Remove url_expires_at column from transaction_attachments table."""
    logger.info("Removing url_expires_at column from transaction_attachments table...")
    
    if engine:
        # Use provided engine for connection
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        db_session = Session()
    else:
        _, db_session = create_engine_and_session()
    
    try:
        # Check if column exists before dropping
        result = db_session.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'transaction_attachments'
            AND column_name = 'url_expires_at'
        """))
        
        column_exists = result.fetchone()[0] > 0
        
        if not column_exists:
            logger.info("Column url_expires_at doesn't exist, skipping removal")
            return
        
        # Drop index first
        db_session.execute(text("""
            DROP INDEX IF EXISTS idx_transaction_attachments_url_expires_at 
            ON transaction_attachments
        """))
        
        # Drop column
        db_session.execute(text("""
            ALTER TABLE transaction_attachments 
            DROP COLUMN url_expires_at
        """))
        
        db_session.commit()
        logger.info("Successfully removed url_expires_at column from transaction_attachments table")
        
    except Exception as e:
        db_session.rollback()
        logger.error("Error removing url_expires_at column from transaction_attachments table: %s", e)
        raise
    finally:
        db_session.close()

if __name__ == "__main__":
    # Run upgrade when script is executed directly
    upgrade()
