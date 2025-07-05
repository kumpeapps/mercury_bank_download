#!/usr/bin/env python3
"""
Test script to create sample transactions with sub-categories for testing the new functionality.
"""

import os
import sys
sys.path.append('/Users/justinkumpe/Documents/mercury_bank_download/web_app')

from models.base import create_engine_and_session
from models.transaction import Transaction
from models.account import Account
from models.mercury_account import MercuryAccount
from datetime import datetime, timedelta
import random

def create_test_transactions():
    # Create database session
    engine, Session = create_engine_and_session()
    session = Session()
    
    try:
        # Get the first account for testing
        account = session.query(Account).first()
        if not account:
            print("No accounts found. Cannot create test transactions.")
            return
        
        print(f"Creating test transactions for account: {account.name}")
        
        # Sample categories with sub-categories
        test_categories = [
            "Office/Supplies",
            "Office/Equipment", 
            "Office/Software",
            "Travel/Flights",
            "Travel/Hotels",
            "Travel/Meals",
            "Marketing/Advertising",
            "Marketing/Content",
            "Marketing/Events",
            "Utilities/Internet",
            "Utilities/Phone",
            "Utilities/Electricity",
            "Food/Groceries",
            "Food/Restaurants", 
            "Entertainment/Movies",
            "Entertainment/Sports",
            "Transportation/Fuel",
            "Transportation/Maintenance",
            "Healthcare/Insurance",
            "Healthcare/Dental",
            "Professional Services/Legal",
            "Professional Services/Accounting",
            "Professional Services/Consulting"
        ]
        
        # Create test transactions
        created_count = 0
        base_date = datetime.now() - timedelta(days=90)  # Start 90 days ago
        
        for i in range(50):  # Create 50 test transactions
            # Random date within the last 90 days
            random_days = random.randint(0, 90)
            transaction_date = base_date + timedelta(days=random_days)
            
            # Random category
            category = random.choice(test_categories)
            
            # Random amount (negative for expenses)
            amount = -random.uniform(10.00, 500.00)
            
            # Create transaction
            transaction = Transaction(
                id=f"test_transaction_{i}_{int(transaction_date.timestamp())}",
                account_id=account.id,
                amount=amount,
                currency="USD",
                description=f"Test transaction for {category}",
                note=category,
                status="sent",
                posted_at=transaction_date,
                created_at=transaction_date
            )
            
            session.add(transaction)
            created_count += 1
        
        # Commit all transactions
        session.commit()
        print(f"Successfully created {created_count} test transactions with sub-categories")
        
        # Print summary of categories created
        unique_categories = sorted(list(set(test_categories)))
        print(f"\nCategories created:")
        for cat in unique_categories:
            if '/' in cat:
                main, sub = cat.split('/', 1)
                print(f"  {main} → {sub}")
            else:
                print(f"  {cat}")
        
    except Exception as e:
        print(f"Error creating test transactions: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_test_transactions()
