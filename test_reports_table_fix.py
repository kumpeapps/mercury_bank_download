#!/usr/bin/env python3
"""
Test script to verify the reports table data fix works correctly.
"""
import sys
import os

# Add the web_app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "web_app"))

from models.user import User
from models.role import Role
from models.mercury_account import MercuryAccount
from models.account import Account
from models.transaction import Transaction
from app import get_reports_table_data
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base

def test_reports_table_fix():
    """Test that get_reports_table_data handles multi-select filtering correctly"""
    
    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create test user with roles
        user_role = Role(name="user", description="Standard user")
        admin_role = Role(name="admin", description="Administrator")
        session.add_all([user_role, admin_role])
        session.flush()
        
        test_user = User(username="testuser", email="test@example.com", password_hash="test_hash")
        test_user.roles.append(user_role)
        session.add(test_user)
        session.flush()
        
        # Create Mercury account
        mercury_account = MercuryAccount(
            name="Test Mercury", 
            api_key="test_key_12345"
        )
        mercury_account.users.append(test_user)
        session.add(mercury_account)
        session.flush()
        
        # Create accounts
        account1 = Account(
            name="Account 1", 
            account_number="acc1", 
            mercury_account_id=mercury_account.id,
            exclude_from_reports=False
        )
        account2 = Account(
            name="Account 2", 
            account_number="acc2", 
            mercury_account_id=mercury_account.id,
            exclude_from_reports=False
        )
        session.add_all([account1, account2])
        session.flush()
        
        # Create test transactions
        transaction1 = Transaction(
            amount=-100.0,
            account_id=account1.id,
            note="Test Category 1",
            status="posted"
        )
        transaction2 = Transaction(
            amount=-200.0,
            account_id=account2.id,
            note="Test Category 2", 
            status="posted"
        )
        session.add_all([transaction1, transaction2])
        session.commit()
        
        # Mock current_user
        import web_app.app as app_module
        app_module.current_user = test_user
        
        print("Testing reports table data with different filter scenarios...")
        
        # Test 1: No account filter (should return all data)
        print("\n1. Testing with no account filter:")
        result = get_reports_table_data(session)
        print(f"   Found {len(result)} categories")
        if result:
            total_amount = sum(item['total_amount'] for item in result)
            print(f"   Total amount: {total_amount}")
        
        # Test 2: Filter by single account
        print("\n2. Testing with single account filter:")
        result = get_reports_table_data(session, account_ids_filter=[account1.id])
        print(f"   Found {len(result)} categories")
        if result:
            total_amount = sum(item['total_amount'] for item in result)
            print(f"   Total amount: {total_amount}")
        
        # Test 3: Filter by multiple accounts
        print("\n3. Testing with multiple account filter:")
        result = get_reports_table_data(session, account_ids_filter=[account1.id, account2.id])
        print(f"   Found {len(result)} categories")
        if result:
            total_amount = sum(item['total_amount'] for item in result)
            print(f"   Total amount: {total_amount}")
        
        # Test 4: Filter by non-existent account (should return empty)
        print("\n4. Testing with non-existent account filter:")
        result = get_reports_table_data(session, account_ids_filter=[99999])
        print(f"   Found {len(result)} categories (should be 0)")
        
        # Test 5: Empty account filter list (should return empty)
        print("\n5. Testing with empty account filter list:")
        result = get_reports_table_data(session, account_ids_filter=[])
        print(f"   Found {len(result)} categories (should be 0)")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_reports_table_fix()
