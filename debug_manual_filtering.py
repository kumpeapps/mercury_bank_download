#!/usr/bin/env python3
"""
Manual interaction test to debug what's really happening with filtering
"""

import requests
from urllib.parse import urlencode, parse_qs, urlparse

def debug_manual_filtering():
    """Debug what happens when we manually submit filters"""
    base_url = "http://localhost:5001"
    
    login_data = {
        'username': 'testfirstuser',
        'password': 'test'
    }
    
    session = requests.Session()
    
    try:
        # Login
        print("1. Logging in...")
        login_response = session.post(f"{base_url}/login", data=login_data)
        if "dashboard" not in login_response.url:
            print("✗ Login failed")
            return False
        print("✓ Login successful")
        
        # Get initial transactions page
        print("\n2. Loading initial transactions page...")
        initial_response = session.get(f"{base_url}/transactions")
        if initial_response.status_code != 200:
            print(f"✗ Failed to load transactions page: {initial_response.status_code}")
            return False
        
        initial_content = initial_response.text
        print("✓ Initial page loaded")
        
        # Check what accounts are available
        print("\n3. Checking available accounts...")
        import re
        account_matches = re.findall(r'name="account_id" value="([^"]+)"', initial_content)
        print(f"Found {len(account_matches)} accounts: {[acc[:8] + '...' for acc in account_matches[:3]]}")
        
        if not account_matches:
            print("✗ No accounts found on page!")
            return False
        
        # Test scenario: Select first account and submit filter
        print("\n4. Testing filter submission...")
        selected_account = account_matches[0]
        
        # Simulate form submission with selected account
        filter_data = {
            'account_id': [selected_account],
            'status': ['pending', 'sent']  # Default statuses
        }
        
        # Submit using POST (like a real form submission)
        print(f"Submitting filter with account: {selected_account[:8]}...")
        filter_response = session.post(f"{base_url}/transactions", data=filter_data)
        
        print(f"POST response status: {filter_response.status_code}")
        print(f"Final URL: {filter_response.url}")
        
        # Check if we were redirected to GET with params
        if filter_response.history:
            print("Response had redirects:")
            for i, resp in enumerate(filter_response.history):
                print(f"  {i+1}. {resp.status_code} -> {resp.url}")
        
        # Now check the final content
        final_content = filter_response.text
        
        # Check if selected account checkbox is checked
        account_checkbox_pattern = rf'value="{re.escape(selected_account)}"[^>]*checked'
        if re.search(account_checkbox_pattern, final_content):
            print(f"✓ Account {selected_account[:8]}... checkbox IS checked after filter")
        else:
            print(f"✗ Account {selected_account[:8]}... checkbox is NOT checked after filter")
        
        # Also try GET method with query params
        print("\n5. Testing GET method with query params...")
        query_params = urlencode(filter_data, doseq=True)
        get_url = f"{base_url}/transactions?{query_params}"
        print(f"GET URL: {get_url}")
        
        get_response = session.get(get_url)
        print(f"GET response status: {get_response.status_code}")
        
        get_content = get_response.text
        if re.search(account_checkbox_pattern, get_content):
            print(f"✓ GET method: Account {selected_account[:8]}... checkbox IS checked")
        else:
            print(f"✗ GET method: Account {selected_account[:8]}... checkbox is NOT checked")
        
        # Check what current_account_ids the template is receiving
        print("\n6. Debugging template variables...")
        current_account_pattern = r'current_account_ids.*?=.*?\[(.*?)\]'
        match = re.search(current_account_pattern, get_content, re.DOTALL)
        if match:
            print(f"Template current_account_ids: {match.group(1)}")
        else:
            print("Could not find current_account_ids in template")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Manual interaction debugging for transaction filtering")
    print("=" * 60)
    
    debug_manual_filtering()
