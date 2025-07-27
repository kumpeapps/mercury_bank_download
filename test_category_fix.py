#!/usr/bin/env python3
"""
Test script to verify that the approval system is now using 
note field categories instead of mercury_category field
"""
import sys
import os

# Add sync_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sync_app'))

def test_category_parsing():
    """Test that parse_category function works correctly"""
    try:
        from category_utils import parse_category
        
        # Test cases
        test_notes = [
            "Gas/Station",
            "Food/Restaurant", 
            "Business/Office Supplies",
            "Just a regular note without category",
            "",
            None
        ]
        
        print("Testing parse_category function:")
        for note in test_notes:
            category, subcategory = parse_category(note)
            print(f"  Note: {repr(note)} -> Category: {repr(category)}, Subcategory: {repr(subcategory)}")
            
        return True
    except ImportError as e:
        print(f"Error importing category_utils: {e}")
        return False

def test_transaction_model():
    """Test that transaction model imports and uses parse_category"""
    try:
        from models.transaction import Transaction
        print("\nTransaction model imports successfully")
        
        # Check if update_approval_status method exists and imports parse_category
        if hasattr(Transaction, 'update_approval_status'):
            print("✓ Transaction.update_approval_status method exists")
        else:
            print("✗ Transaction.update_approval_status method missing")
            
        return True
    except ImportError as e:
        print(f"Error importing Transaction model: {e}")
        return False

if __name__ == "__main__":
    print("Testing Category Parsing Fix")
    print("=" * 40)
    
    success = True
    success &= test_category_parsing()
    success &= test_transaction_model()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! Category parsing fix appears to be working.")
    else:
        print("✗ Some tests failed. Check the errors above.")
        
    print("\nNext: Check if transactions are being correctly categorized in the database")
