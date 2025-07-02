"""
Create transaction_attachments table for storing attachment metadata.

This migration creates a new table to store detailed information about
attachments associated with transactions from the Mercury Bank API.
"""

from sqlalchemy import text
from models.base import create_engine_and_session
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade(engine=None):
    """Create the transaction_attachments table."""
    logger.info("Creating transaction_attachments table...")
    
    if engine:
        # Use provided engine for connection
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        db_session = Session()
    else:
        _, db_session = create_engine_and_session()
    
    try:
        # Check if table already exists
        result = db_session.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'transaction_attachments'
        """))
        
        table_exists = result.fetchone()[0] > 0
        
        if table_exists:
            logger.info("Table transaction_attachments already exists, skipping creation")
            return
        
        # Create transaction_attachments table
        db_session.execute(text("""
            CREATE TABLE transaction_attachments (
                id VARCHAR(255) PRIMARY KEY,
                transaction_id VARCHAR(255) NOT NULL,
                filename VARCHAR(500),
                content_type VARCHAR(100),
                file_size INT,
                description TEXT,
                mercury_url TEXT,
                thumbnail_url TEXT,
                upload_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                CONSTRAINT fk_transaction_attachments_transaction_id 
                FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
                
                INDEX idx_transaction_attachments_transaction_id (transaction_id),
                INDEX idx_transaction_attachments_filename (filename),
                INDEX idx_transaction_attachments_content_type (content_type),
                INDEX idx_transaction_attachments_upload_date (upload_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        
        db_session.commit()
        logger.info("Successfully created transaction_attachments table")
        
    except Exception as e:
        db_session.rollback()
        logger.error("Error creating transaction_attachments table: %s", e)
        raise
    finally:
        db_session.close()

def downgrade(engine=None):
    """Drop the transaction_attachments table."""
    logger.info("Dropping transaction_attachments table...")
    
    if engine:
        # Use provided engine for connection
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        db_session = Session()
    else:
        _, db_session = create_engine_and_session()
    
    try:
        # Check if table exists before dropping
        result = db_session.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'transaction_attachments'
        """))
        
        table_exists = result.fetchone()[0] > 0
        
        if not table_exists:
            logger.info("Table transaction_attachments does not exist, skipping drop")
            return
        
        # Drop the table
        db_session.execute(text("DROP TABLE transaction_attachments"))
        
        db_session.commit()
        logger.info("Successfully dropped transaction_attachments table")
        
    except Exception as e:
        db_session.rollback()
        logger.error("Error dropping transaction_attachments table: %s", e)
        raise
    finally:
        db_session.close()

if __name__ == "__main__":
    upgrade()
