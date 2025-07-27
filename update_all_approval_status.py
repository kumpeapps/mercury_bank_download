#!/usr/bin/env python3
"""
Script to update approval status for all existing transactions.
"""

import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the sync_app directory to the path so we can import models
sys.path.append('/app')

# Import models and manager
from models import Transaction
from transaction_approval_manager import TransactionApprovalManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Update approval status for all transactions."""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return 1
    
    logger.info(f"Connecting to database: {database_url}")
    
    try:
        # Create database engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        
        # Get all transactions
        transactions = db_session.query(Transaction).all()
        logger.info(f"Found {len(transactions)} transactions to update")
        
        # Update approval status for each transaction
        updated_count = 0
        for transaction in transactions:
            try:
                old_status = transaction.approval_status
                transaction.update_approval_status(db_session)
                new_status = transaction.approval_status
                
                if old_status != new_status:
                    logger.info(f"Transaction {transaction.id}: {old_status} -> {new_status}")
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to update transaction {transaction.id}: {str(e)}")
        
        # Commit all changes
        db_session.commit()
        logger.info(f"Successfully updated {updated_count} transactions")
        
        db_session.close()
        return 0
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
