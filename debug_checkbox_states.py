#!/usr/bin/env python3
"""
Debug script to examine HTML output for checkbox states
"""

import requests
from urllib.parse import urlencode

def debug_checkbox_states():
    """Debug checkbox states in HTML output"""
    base_url = "http://localhost:5001"
    
    login_data = {
        'username': 'testfirstuser',
        'password': 'testpass123'
    }
    
    session = requests.Session()
    
    try:
        # Login
        login_response = session.post(f"{base_url}/login", data=login_data)
        if login_response.status_code != 200:
            print("Login failed")
            return
        
        # Test with specific account filter
        params = {
            'account_id': ['867a1270-54fe-11f0-9652-b7f2a577d83a']
        }
        query_string = urlencode(params, doseq=True)
        test_url = f"{base_url}/transactions?{query_string}"
        
        print(f"Testing URL: {test_url}")
        
        response = session.get(test_url)
        content = response.text
        
        # Find all account checkboxes
        account_id = '867a1270-54fe-11f0-9652-b7f2a577d83a'
        
        # Look for the specific account checkbox
        search_start = content.find(f'value="{account_id}"')
        if search_start == -1:
            print(f"Account {account_id} not found in HTML")
            return
        
        # Get context around the checkbox
        context_start = max(0, search_start - 200)
        context_end = min(len(content), search_start + 200)
        context = content[context_start:context_end]
        
        print(f"\nHTML context around account {account_id[:8]}...:")
        print("-" * 80)
        print(context)
        print("-" * 80)
        
        # Check if 'checked' appears in this context
        if 'checked' in context:
            print("✓ 'checked' attribute found in context")
        else:
            print("✗ 'checked' attribute NOT found in context")
            
        # Also look for all input elements with account_id name
        print("\nAll account_id inputs:")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'name="account_id"' in line:
                print(f"Line {i}: {line.strip()}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_checkbox_states()
