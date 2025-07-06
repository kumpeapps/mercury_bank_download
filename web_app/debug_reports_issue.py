#!/usr/bin/env python3
"""
Debug script to test the reports issue with testfirstuser
"""

import os
import sys

# Add the web_app directory to Python path
sys.path.insert(0, '/app')

from models import User, MercuryAccount, Account, Transaction
from app import Session, get_hierarchical_reports_data
from app import get_hierarchical_reports_data

def debug_reports_issue():
    """Debug the reports issue by simulating what happens when testfirstuser accesses reports"""
    
    # Create database session
    db_session = Session()
    
    try:
        # Get the user
        user = db_session.query(User).filter_by(username='testfirstuser').first()
        if not user:
            print("ERROR: testfirstuser not found!")
            return
            
        print(f"User found: {user.username} (ID: {user.id})")
        
        # Get user's Mercury accounts
        mercury_accounts = (
            db_session.query(MercuryAccount)
            .filter(MercuryAccount.users.contains(user))
            .all()
        )
        
        print(f"User has access to {len(mercury_accounts)} Mercury accounts:")
        for ma in mercury_accounts:
            print(f"  - {ma.name} (ID: {ma.id})")
            
        # Get accounts for each Mercury account
        all_account_ids = []
        for mercury_account in mercury_accounts:
            accounts = (
                db_session.query(Account)
                .filter_by(mercury_account_id=mercury_account.id)
                .filter_by(exclude_from_reports=False)
                .all()
            )
            account_ids = [acc.id for acc in accounts]
            all_account_ids.extend(account_ids)
            print(f"  Mercury account {mercury_account.name} has {len(accounts)} accounts (not excluded from reports)")
            
        print(f"Total account IDs for reports: {len(all_account_ids)}")
        print(f"Account IDs: {all_account_ids[:3]}...")  # Show first 3
        
        # Test the hierarchical reports function directly
        print("\n=== Testing get_hierarchical_reports_data ===")
        
        # Simulate current_user for the function
        import app
        app.current_user = user
        
        # Call the function without any filters
        hierarchical_data = get_hierarchical_reports_data(
            db_session=db_session,
            mercury_account_id=None,
            month_filter=None,
            account_ids_filter=None,
            category=None,
            expanded_status_filter=None,
        )
        
        print(f"Hierarchical data returned: {len(hierarchical_data)} categories")
        for i, cat_data in enumerate(hierarchical_data[:5]):  # Show first 5
            print(f"  {i+1}. {cat_data['main_category']}: ${cat_data['total_amount']:.2f} ({cat_data['transaction_count']} transactions)")
            
        # Test with specific filters (sent + pending)
        print("\n=== Testing with default status filter (sent + pending) ===")
        hierarchical_data_filtered = get_hierarchical_reports_data(
            db_session=db_session,
            mercury_account_id=None,
            month_filter=None,
            account_ids_filter=None,
            category=None,
            expanded_status_filter=['sent', 'pending'],
        )
        
        print(f"Hierarchical data with status filter: {len(hierarchical_data_filtered)} categories")
        
        # Check what statuses exist in the transactions
        print("\n=== Checking available transaction statuses ===")
        statuses = db_session.query(Transaction.status).filter(
            Transaction.account_id.in_(all_account_ids)
        ).distinct().all()
        
        print("Available statuses:")
        for status in statuses:
            if status[0]:
                count = db_session.query(Transaction).filter(
                    Transaction.account_id.in_(all_account_ids),
                    Transaction.status == status[0]
                ).count()
                print(f"  - {status[0]}: {count} transactions")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_session.close()

if __name__ == "__main__":
    debug_reports_issue()
