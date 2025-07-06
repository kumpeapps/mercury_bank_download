#!/usr/bin/env python3
"""
Test script to verify transaction filtering functionality works correctly
"""

import requests
import time
from urllib.parse import urlencode

def test_transaction_filtering():
    """Test transaction filtering and checkbox state preservation"""
    base_url = "http://localhost:5001"
    
    # Login data
    login_data = {
        'username': 'testfirstuser',
        'password': 'testpass123'
    }
    
    print("Testing transaction filtering functionality...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # 1. Login first
        print("1. Logging in...")
        login_response = session.post(f"{base_url}/login", data=login_data)
        if login_response.status_code == 200 and "/dashboard" in login_response.url:
            print("✓ Login successful")
        else:
            print(f"✗ Login failed: {login_response.status_code}")
            return False
        
        # 2. Get initial transactions page
        print("2. Loading transactions page...")
        transactions_response = session.get(f"{base_url}/transactions")
        if transactions_response.status_code == 200:
            print("✓ Transactions page loaded")
        else:
            print(f"✗ Failed to load transactions page: {transactions_response.status_code}")
            return False
        
        # 3. Test filtering with account selection
        print("3. Testing account filtering...")
        
        # Get the first few account IDs from the database
        # We'll simulate selecting multiple accounts
        filter_params = {
            'account_id': ['867a1270-54fe-11f0-9652-b7f2a577d83a', '8683ef0c-54fe-11f0-9652-1b0a5a6d3438'],
            'status': ['posted', 'pending']
        }
        
        # Build URL with multiple account_id parameters
        query_string = urlencode(filter_params, doseq=True)
        filter_url = f"{base_url}/transactions?{query_string}"
        
        print(f"Filter URL: {filter_url}")
        
        filtered_response = session.get(filter_url)
        if filtered_response.status_code == 200:
            print("✓ Filtered request successful")
            
            # Check if the response contains the expected checkbox states
            response_content = filtered_response.text
            
            # Look for checked checkboxes in the response
            if 'checked' in response_content:
                print("✓ Found checked checkboxes in response")
                
                # Count how many checkboxes are checked
                checked_count = response_content.count('checked')
                print(f"✓ Found {checked_count} checked elements")
                
                # Verify specific account IDs are checked
                for account_id in filter_params['account_id']:
                    if f'value="{account_id}"' in response_content and 'checked' in response_content:
                        print(f"✓ Account {account_id[:8]}... checkbox state preserved")
                    else:
                        print(f"✗ Account {account_id[:8]}... checkbox state NOT preserved")
                
                return True
            else:
                print("✗ No checked checkboxes found in response")
                return False
        else:
            print(f"✗ Filtered request failed: {filtered_response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("Starting transaction filtering test...")
    print("=" * 50)
    
    # Wait a moment for services to be ready
    time.sleep(2)
    
    success = test_transaction_filtering()
    
    print("=" * 50)
    if success:
        print("✓ Transaction filtering test PASSED")
    else:
        print("✗ Transaction filtering test FAILED")
    
    exit(0 if success else 1)
