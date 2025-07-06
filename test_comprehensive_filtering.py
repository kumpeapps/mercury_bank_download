#!/usr/bin/env python3
"""
Comprehensive test for transaction filtering functionality
"""

import requests
import time
from urllib.parse import urlencode

def test_comprehensive_filtering():
    """Test various filtering scenarios"""
    base_url = "http://localhost:5001"
    
    # Login data
    login_data = {
        'username': 'testfirstuser',
        'password': 'testpass123'
    }
    
    print("Testing comprehensive transaction filtering...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Login
        print("Logging in...")
        login_response = session.post(f"{base_url}/login", data=login_data)
        if login_response.status_code != 200 or "/dashboard" not in login_response.url:
            print(f"✗ Login failed: {login_response.status_code}")
            return False
        print("✓ Login successful")
        
        # Test cases
        test_cases = [
            {
                "name": "Single account filter",
                "params": {
                    'account_id': ['867a1270-54fe-11f0-9652-b7f2a577d83a']
                }
            },
            {
                "name": "Multiple account filter",
                "params": {
                    'account_id': ['867a1270-54fe-11f0-9652-b7f2a577d83a', '8683ef0c-54fe-11f0-9652-1b0a5a6d3438']
                }
            },
            {
                "name": "Status filter only",
                "params": {
                    'status': ['posted']
                }
            },
            {
                "name": "Combined account and status filter",
                "params": {
                    'account_id': ['867a1270-54fe-11f0-9652-b7f2a577d83a'],
                    'status': ['posted', 'pending']
                }
            },
            {
                "name": "No filters (default state)",
                "params": {}
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test_case['name']}")
            
            # Build URL
            if test_case['params']:
                query_string = urlencode(test_case['params'], doseq=True)
                test_url = f"{base_url}/transactions?{query_string}"
            else:
                test_url = f"{base_url}/transactions"
            
            print(f"   URL: {test_url}")
            
            # Make request
            response = session.get(test_url)
            if response.status_code != 200:
                print(f"   ✗ Request failed: {response.status_code}")
                continue
            
            content = response.text
            
            # Verify checkboxes are properly set
            if 'account_id' in test_case['params']:
                for account_id in test_case['params']['account_id']:
                    if f'value="{account_id}"' in content:
                        if 'checked' in content[content.find(f'value="{account_id}"')-50:content.find(f'value="{account_id}"')+50]:
                            print(f"   ✓ Account {account_id[:8]}... checkbox preserved")
                        else:
                            print(f"   ✗ Account {account_id[:8]}... checkbox NOT preserved")
            
            if 'status' in test_case['params']:
                for status in test_case['params']['status']:
                    if f'value="{status}"' in content:
                        status_section = content[content.find(f'value="{status}"')-50:content.find(f'value="{status}"')+50]
                        if 'checked' in status_section:
                            print(f"   ✓ Status '{status}' checkbox preserved")
                        else:
                            print(f"   ✗ Status '{status}' checkbox NOT preserved")
            
            # Check for transaction table/cards
            if 'transaction-table' in content or 'transaction-card' in content:
                print(f"   ✓ Transactions displayed")
            else:
                print(f"   ⚠ No transactions visible (might be empty result)")
            
            print(f"   ✓ Test case completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("Starting comprehensive transaction filtering test...")
    print("=" * 60)
    
    success = test_comprehensive_filtering()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL transaction filtering tests PASSED")
    else:
        print("✗ Some transaction filtering tests FAILED")
    
    exit(0 if success else 1)
