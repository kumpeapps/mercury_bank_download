#!/usr/bin/env python3
"""
Direct database test to verify sub-category logic without authentication.
"""

import sys
sys.path.append('/Users/justinkumpe/Documents/mercury_bank_download/web_app')

from models.base import create_engine_and_session
from models.transaction import Transaction
from models.account import Account
from app import parse_category, format_category_display

def test_subcategory_display():
    """Test how sub-categories are displayed in the table data."""
    print("Testing sub-category display logic...")
    
    # Create database session
    engine, Session = create_engine_and_session()
    session = Session()
    
    try:
        # Get all accounts
        accounts = session.query(Account).all()
        if not accounts:
            print("No accounts found")
            return
        
        # Get transactions with categories directly
        transactions = session.query(Transaction).filter(
            Transaction.note.isnot(None),
            Transaction.note != ""
        ).limit(20).all()
        
        print(f"Found {len(transactions)} transactions with categories")
        
        # Check for sub-categories and test formatting
        subcategory_count = 0
        for tx in transactions:
            if tx.note and '/' in tx.note:
                formatted = format_category_display(tx.note)
                subcategory_count += 1
                print(f"  Sub-category: {tx.note} → Display: {formatted}")
        
        print(f"Found {subcategory_count} sub-categories with formatted display")
        
        # Test individual formatting
        print("\nTesting individual category formatting:")
        test_categories = [
            "Office/Supplies",
            "Travel/Hotels", 
            "Food/Restaurants",
            "Office",
            "Entertainment"
        ]
        
        for cat in test_categories:
            main_cat, sub_cat = parse_category(cat)
            formatted = format_category_display(cat)
            print(f"  {cat} → {main_cat}, {sub_cat} → {formatted}")
        
        # Query some actual transactions to see their categories
        print("\nSample transaction categories from database:")
        transactions = session.query(Transaction.note).filter(
            Transaction.note.isnot(None)
        ).distinct().limit(10).all()
        
        for tx in transactions:
            if tx[0]:
                formatted = format_category_display(tx[0])
                print(f"  {tx[0]} → {formatted}")
        
        print("✓ Sub-category display logic test complete")
        
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_subcategory_display()
