#!/usr/bin/env python3
"""
Update approval status for all transactions based on current restrictions.

This script evaluates all transactions in the database against the current
transaction restrictions and updates their approval_status field accordingly.
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add sync_app to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Transaction, Base
from transaction_approval_manager import TransactionApprovalManager

def main():
    """Main function to update approval status for all transactions."""
    # Database connection - use environment variable or default for Docker
    database_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:password@mysql:3306/mercury_bank')
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Starting approval status update for all transactions...")
        
        # Get all transactions that need status evaluation
        # Focus on recent transactions that might need approval
        cutoff_date = datetime.utcnow() - timedelta(days=90)  # Last 90 days
        
        transactions = db.query(Transaction).filter(
            Transaction.created_at >= cutoff_date
        ).all()
        
        print(f"Found {len(transactions)} transactions to evaluate")
        
        updated_count = 0
        for transaction in transactions:
            original_status = transaction.approval_status
            
            try:
                # Update approval status
                transaction.update_approval_status(db)
                
                if transaction.approval_status != original_status:
                    updated_count += 1
                    print(f"Transaction {transaction.id}: {original_status} -> {transaction.approval_status}")
                    
            except Exception as e:
                print(f"Error updating transaction {transaction.id}: {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        print(f"\nSuccessfully updated {updated_count} transactions")
        
        # Show summary of approval statuses
        print("\nApproval status summary:")
        status_counts = db.query(Transaction.approval_status, db.func.count(Transaction.id)).group_by(Transaction.approval_status).all()
        for status, count in status_counts:
            print(f"  {status}: {count} transactions")
            
    except Exception as e:
        print(f"Error during approval status update: {str(e)}")
        db.rollback()
        raise
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
