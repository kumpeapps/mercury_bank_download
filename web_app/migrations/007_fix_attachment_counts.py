"""
Migration: Fix transaction attachment counts

This migration ensures that the number_of_attachments field on transactions
matches the actual count of attachments in the transaction_attachments table.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models.base import create_engine_and_session
import logging

logger = logging.getLogger(__name__)

def upgrade(db_session=None):
    """Fix transaction attachment counts to match actual attachments."""
    try:
        engine, SessionLocal = create_engine_and_session()
        session = SessionLocal()
        
        # Update all transactions to have correct attachment counts
        result = session.execute(text("""
            UPDATE transactions t
            SET number_of_attachments = (
                SELECT COUNT(*)
                FROM transaction_attachments ta
                WHERE ta.transaction_id = t.id
            )
            WHERE t.number_of_attachments != (
                SELECT COUNT(*)
                FROM transaction_attachments ta
                WHERE ta.transaction_id = t.id
            )
        """))
        
        rows_updated = result.rowcount
        session.commit()
        
        logger.info(f"Fixed attachment counts for {rows_updated} transactions")
        print(f"✅ Fixed attachment counts for {rows_updated} transactions")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Error fixing attachment counts: {e}")
        print(f"❌ Error fixing attachment counts: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def downgrade(db_session=None):
    """This migration cannot be reversed as it only fixes data consistency."""
    logger.info("This migration cannot be reversed - it only fixes data consistency")
    print("ℹ️  This migration cannot be reversed - it only fixes data consistency")
    return True

if __name__ == "__main__":
    print("Running attachment count fix migration...")
    success = upgrade()
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")
