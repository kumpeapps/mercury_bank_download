"""
Add primary_account_id column to user_settings table

This migration adds the primary_account_id column to the user_settings table
to maintain consistency between sync_app and web_app schemas.
"""

from sqlalchemy import Column, String, ForeignKey, MetaData, Table, text
import logging

logger = logging.getLogger(__name__)


def upgrade(engine):
    """Add primary_account_id column to user_settings table"""
    
    logger.info("Adding primary_account_id column to user_settings table...")
    
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Check if user_settings table exists
    if 'user_settings' not in metadata.tables:
        logger.warning("user_settings table does not exist, skipping migration")
        return
        
    user_settings_table = metadata.tables['user_settings']
    
    # Check if primary_account_id column already exists
    if 'primary_account_id' in [col.name for col in user_settings_table.columns]:
        logger.info("primary_account_id column already exists, skipping")
        return
    
    # Add the column using raw SQL to avoid SQLAlchemy model dependencies
    with engine.connect() as conn:
        try:
            # Add the column
            conn.execute(text("ALTER TABLE user_settings ADD COLUMN primary_account_id VARCHAR(255) NULL"))
            
            # Add the foreign key constraint if accounts table exists
            if 'accounts' in metadata.tables:
                try:
                    conn.execute(text("""
                        ALTER TABLE user_settings 
                        ADD CONSTRAINT fk_user_settings_primary_account_id 
                        FOREIGN KEY (primary_account_id) REFERENCES accounts(id)
                    """))
                    logger.info("Added foreign key constraint for primary_account_id")
                except Exception as e:
                    logger.warning(f"Could not add foreign key constraint for primary_account_id: {e}")
            else:
                logger.warning("accounts table does not exist, skipping foreign key constraint")
            
            conn.commit()
            logger.info("Successfully added primary_account_id column to user_settings table")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding primary_account_id column: {e}")
            raise


def downgrade(engine):
    """Remove primary_account_id column from user_settings table"""
    
    logger.info("Removing primary_account_id column from user_settings table...")
    
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Check if user_settings table exists
    if 'user_settings' not in metadata.tables:
        logger.warning("user_settings table does not exist, skipping migration")
        return
        
    user_settings_table = metadata.tables['user_settings']
    
    # Check if primary_account_id column exists
    if 'primary_account_id' not in [col.name for col in user_settings_table.columns]:
        logger.info("primary_account_id column does not exist, skipping")
        return
    
    # Remove the column using raw SQL
    with engine.connect() as conn:
        try:
            # Drop foreign key constraint first
            try:
                conn.execute(text("ALTER TABLE user_settings DROP FOREIGN KEY fk_user_settings_primary_account_id"))
                logger.info("Dropped foreign key constraint for primary_account_id")
            except Exception as e:
                logger.warning(f"Could not drop foreign key constraint: {e}")
            
            # Drop the column
            conn.execute(text("ALTER TABLE user_settings DROP COLUMN primary_account_id"))
            
            conn.commit()
            logger.info("Successfully removed primary_account_id column from user_settings table")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error removing primary_account_id column: {e}")
            raise
