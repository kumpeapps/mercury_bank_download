#!/usr/bin/env python3
"""
Detailed analysis of checkbox states
"""

import requests
import re

def analyze_checkbox_states():
    """Analyze checkbox states in detail"""
    base_url = "http://localhost:5001"
    
    login_data = {
        'username': 'testfirstuser',
        'password': 'testpass123'
    }
    
    session = requests.Session()
    
    try:
        # Login
        login_response = session.post(f"{base_url}/login", data=login_data)
        if "dashboard" not in login_response.url:
            print("Login failed")
            return False
        
        # Get accounts
        initial_response = session.get(f"{base_url}/transactions")
        accounts = re.findall(r'name="account_id" value="([^"]+)"', initial_response.text)
        
        if not accounts:
            print("No accounts found")
            return False
        
        target_account = accounts[0]
        print(f"Testing with account: {target_account[:8]}...")
        
        # Filter with account
        filter_url = f"{base_url}/transactions?account_id={target_account}"
        filter_response = session.get(filter_url)
        content = filter_response.text
        
        print(f"Response status: {filter_response.status_code}")
        
        # Find ALL input elements with name="account_id"
        print("\nAll account_id input elements:")
        input_pattern = r'<input[^>]*name="account_id"[^>]*>'
        inputs = re.findall(input_pattern, content)
        
        for i, input_elem in enumerate(inputs):
            print(f"{i+1}. {input_elem}")
            if 'checked' in input_elem:
                value_match = re.search(r'value="([^"]+)"', input_elem)
                if value_match:
                    account_id = value_match.group(1)
                    print(f"   -> CHECKED account: {account_id[:8]}...")
        
        # Check specifically for our target account
        print(f"\nLooking specifically for account {target_account[:8]}...")
        target_pattern = rf'<input[^>]*name="account_id"[^>]*value="{re.escape(target_account)}"[^>]*>'
        target_match = re.search(target_pattern, content)
        
        if target_match:
            target_input = target_match.group(0)
            print(f"Found target input: {target_input}")
            if 'checked' in target_input:
                print("✓ Target account checkbox IS checked")
            else:
                print("✗ Target account checkbox is NOT checked")
        else:
            print("✗ Target account input not found")
        
        # Let's also check what current_account_ids the backend is passing
        print("\nChecking backend template context...")
        
        # Look for the template render in a different way
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'current_account_ids' in line:
                print(f"Line {i}: {line.strip()}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Detailed checkbox state analysis")
    print("=" * 40)
    
    analyze_checkbox_states()
