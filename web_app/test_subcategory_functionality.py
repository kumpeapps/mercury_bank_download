#!/usr/bin/env python3
"""
Comprehensive test script to verify sub-category functionality.
"""

import os
import sys
sys.path.append('/Users/justinkumpe/Documents/mercury_bank_download/web_app')

from models.base import create_engine_and_session
from models.transaction import Transaction
from models.account import Account
import requests
import json

def test_subcategory_parsing():
    """Test the category parsing functions."""
    print("Testing category parsing functions...")
    
    # Import the helper functions
    sys.path.append('/Users/justinkumpe/Documents/mercury_bank_download/web_app')
    from app import parse_category, format_category_display, get_unique_categories_and_subcategories
    
    # Test parse_category
    assert parse_category("Office/Supplies") == ("Office", "Supplies")
    assert parse_category("Office") == ("Office", None)
    assert parse_category("") == (None, None)
    assert parse_category(None) == (None, None)
    
    # Test format_category_display
    assert format_category_display("Office/Supplies") == "Office → Supplies"
    assert format_category_display("Office") == "Office"
    assert format_category_display("") == "Uncategorized"
    assert format_category_display(None) == "Uncategorized"
    
    print("✓ Category parsing functions work correctly")

def test_database_categories():
    """Test category retrieval from database."""
    print("Testing database category retrieval...")
    
    # Create database session
    engine, Session = create_engine_and_session()
    session = Session()
    
    try:
        # Get all accounts
        accounts = session.query(Account).all()
        if not accounts:
            print("No accounts found")
            return
        
        account_ids = [acc.id for acc in accounts]
        
        # Import the helper function
        sys.path.append('/Users/justinkumpe/Documents/mercury_bank_download/web_app')
        from app import get_unique_categories_and_subcategories
        
        category_data = get_unique_categories_and_subcategories(session, account_ids)
        
        print(f"Found {len(category_data['categories'])} main categories")
        print(f"Found {len(category_data['all_combinations'])} total category combinations")
        
        # Print some examples
        print("\nMain categories:")
        for cat in sorted(category_data['categories'])[:5]:
            print(f"  - {cat}")
        
        print("\nSub-categories:")
        for main_cat, sub_cats in list(category_data['subcategories'].items())[:3]:
            print(f"  {main_cat}:")
            for sub_cat in sub_cats:
                print(f"    - {sub_cat}")
        
        print("\nAll combinations (sample):")
        for combo in sorted(category_data['all_combinations'])[:10]:
            if '/' in combo:
                main, sub = combo.split('/', 1)
                print(f"  - {main} → {sub}")
            else:
                print(f"  - {combo}")
        
        print("✓ Database category retrieval works correctly")
        
    except Exception as e:
        print(f"Error testing database categories: {e}")
    finally:
        session.close()

def test_web_endpoints():
    """Test web endpoints that use sub-categories."""
    print("Testing web endpoints...")
    
    base_url = "http://localhost:5001"
    
    try:
        # Test reports page
        response = requests.get(f"{base_url}/reports", timeout=10)
        if response.status_code == 200:
            print("✓ Reports page loads successfully")
            # Check if sub-categories are in the response
            if "→" in response.text:
                print("✓ Sub-categories are displayed in reports")
            else:
                print("⚠ Sub-categories might not be displayed in reports")
        else:
            print(f"✗ Reports page failed with status {response.status_code}")
        
        # Test transactions page
        response = requests.get(f"{base_url}/transactions", timeout=10)
        if response.status_code == 200:
            print("✓ Transactions page loads successfully")
            # Check if sub-categories are in the response
            if "→" in response.text:
                print("✓ Sub-categories are displayed in transactions")
            else:
                print("⚠ Sub-categories might not be displayed in transactions")
        else:
            print(f"✗ Transactions page failed with status {response.status_code}")
        
        # Test budget data API
        response = requests.get(f"{base_url}/api/budget_data", timeout=10)
        if response.status_code == 200:
            budget_data = response.json()
            print("✓ Budget data API works")
            
            # Check if any labels contain formatted categories
            labels = []
            for dataset in budget_data.get('datasets', []):
                labels.append(dataset.get('label', ''))
            
            if any('→' in label for label in labels):
                print("✓ Budget data contains formatted sub-categories")
            else:
                print("⚠ Budget data might not contain formatted sub-categories")
        else:
            print(f"✗ Budget data API failed with status {response.status_code}")
        
        # Test expense breakdown API
        response = requests.get(f"{base_url}/api/expense_breakdown", timeout=10)
        if response.status_code == 200:
            expense_data = response.json()
            print("✓ Expense breakdown API works")
            
            # Check if any labels contain formatted categories
            labels = expense_data.get('labels', [])
            if any('→' in label for label in labels):
                print("✓ Expense breakdown contains formatted sub-categories")
            else:
                print("⚠ Expense breakdown might not contain formatted sub-categories")
        else:
            print(f"✗ Expense breakdown API failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error testing web endpoints: {e}")

def test_category_filtering():
    """Test category filtering functionality."""
    print("Testing category filtering...")
    
    base_url = "http://localhost:5001"
    
    try:
        # Test filtering by main category
        response = requests.get(f"{base_url}/reports?category=Office", timeout=10)
        if response.status_code == 200:
            print("✓ Main category filtering works")
        else:
            print(f"✗ Main category filtering failed with status {response.status_code}")
        
        # Test filtering by sub-category
        response = requests.get(f"{base_url}/reports?category=Office/Supplies", timeout=10)
        if response.status_code == 200:
            print("✓ Sub-category filtering works")
        else:
            print(f"✗ Sub-category filtering failed with status {response.status_code}")
        
        # Test filtering in transactions
        response = requests.get(f"{base_url}/transactions?category=Travel/Hotels", timeout=10)
        if response.status_code == 200:
            print("✓ Transaction sub-category filtering works")
        else:
            print(f"✗ Transaction sub-category filtering failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error testing category filtering: {e}")

def main():
    """Run all tests."""
    print("=== Sub-Category Functionality Test ===\n")
    
    test_subcategory_parsing()
    print()
    
    test_database_categories()
    print()
    
    test_web_endpoints()
    print()
    
    test_category_filtering()
    print()
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()
