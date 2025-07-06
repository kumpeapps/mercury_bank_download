#!/usr/bin/env python3
"""
Test script to verify multi-select account filter functionality
"""

import requests

def test_multiselect_filter():
    """Test the multi-select account filter via HTTP requests"""
    base_url = "http://localhost:5001"
    
    # Test data
    login_data = {
        'username': 'testfirstuser',
        'password': 'testpass123'
    }
    
    print("Testing multi-select account filter functionality...")
    
    with requests.Session() as session:
        # Login
        print("1. Logging in...")
        login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        
        if login_response.status_code == 302:
            print("✅ Login successful")
        else:
            print(f"❌ Login failed with status {login_response.status_code}")
            return False
        
        # Test transactions page with no filter
        print("2. Testing transactions page without account filter...")
        transactions_response = session.get(f"{base_url}/transactions")
        
        if transactions_response.status_code == 200:
            print("✅ Transactions page loads successfully")
            
            # Check if the page contains the multi-select structure
            if 'type="checkbox"' in transactions_response.text and 'name="account_id"' in transactions_response.text:
                print("✅ Multi-select account filter detected in HTML")
            else:
                print("❌ Multi-select account filter not found in HTML")
                return False
        else:
            print(f"❌ Transactions page failed with status {transactions_response.status_code}")
            return False
        
        # Test transactions page with multiple account filters (simulated)
        print("3. Testing transactions page with multiple account IDs...")
        multi_account_params = {
            'account_id': ['123', '456'],  # These would be real account IDs in a real test
            'status': ['pending', 'posted']
        }
        
        multi_response = session.get(f"{base_url}/transactions", params=multi_account_params)
        
        if multi_response.status_code == 200:
            print("✅ Transactions page accepts multiple account_id parameters")
        else:
            print(f"❌ Multiple account filter failed with status {multi_response.status_code}")
            return False
        
        # Test reports page with no filter
        print("4. Testing reports page without account filter...")
        reports_response = session.get(f"{base_url}/reports")
        
        if reports_response.status_code == 200:
            print("✅ Reports page loads successfully")
            
            # Check if the page contains the multi-select structure
            if 'type="checkbox"' in reports_response.text and 'name="account_id"' in reports_response.text:
                print("✅ Multi-select account filter detected in reports HTML")
            else:
                print("❌ Multi-select account filter not found in reports HTML")
                return False
        else:
            print(f"❌ Reports page failed with status {reports_response.status_code}")
            return False
        
        # Test reports page with multiple account filters (simulated)
        print("5. Testing reports page with multiple account IDs...")
        reports_multi_response = session.get(f"{base_url}/reports", params=multi_account_params)
        
        if reports_multi_response.status_code == 200:
            print("✅ Reports page accepts multiple account_id parameters")
        else:
            print(f"❌ Multiple account filter failed on reports with status {reports_multi_response.status_code}")
            return False
        
        print("\n🎉 All multi-select filter tests passed!")
        return True

if __name__ == "__main__":
    success = test_multiselect_filter()
    exit(0 if success else 1)
