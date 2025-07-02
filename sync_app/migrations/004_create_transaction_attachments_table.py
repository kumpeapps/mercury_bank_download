"""
Create transaction_attachments table for storing attachment metadata.

This migration creates a new table to store detailed information about
attachments associated with transactions from the Mercury Bank API.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from models.base import create_engine_and_session, Base
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
        engine, db_session = create_engine_and_session()
    
    try:
        # Create the table using SQLAlchemy
        from sqlalchemy import MetaData, Table
        
        metadata = MetaData()
        
        # Check if table already exists
        metadata.reflect(bind=engine)
        if 'transaction_attachments' in metadata.tables:
            logger.info("Table transaction_attachments already exists, skipping creation")
            return
        
        # Define the table structure using SQLAlchemy
        transaction_attachments = Table(
            'transaction_attachments',
            metadata,
            Column('id', String(255), primary_key=True),
            Column('transaction_id', String(255), ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False),
            Column('filename', String(500)),
            Column('content_type', String(100)),
            Column('file_size', Integer),
            Column('description', Text),
            Column('mercury_url', Text),
            Column('thumbnail_url', Text),
            Column('upload_date', DateTime),
            Column('created_at', DateTime, default=func.current_timestamp()),
            Column('updated_at', DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()),
            
            # Indexes
            Index('idx_transaction_attachments_transaction_id', 'transaction_id'),
            Index('idx_transaction_attachments_filename', 'filename'),
            Index('idx_transaction_attachments_content_type', 'content_type'),
            Index('idx_transaction_attachments_upload_date', 'upload_date'),
        )
        
        # Create the table
        transaction_attachments.create(engine)
        
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
        engine, db_session = create_engine_and_session()
    
    try:
        # Drop the table using SQLAlchemy
        from sqlalchemy import MetaData, Table
        
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        if 'transaction_attachments' not in metadata.tables:
            logger.info("Table transaction_attachments does not exist, skipping drop")
            return
        
        # Get the table and drop it
        transaction_attachments = metadata.tables['transaction_attachments']
        transaction_attachments.drop(engine)
        
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
