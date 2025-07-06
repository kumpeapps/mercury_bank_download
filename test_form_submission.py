#!/usr/bin/env python3
"""
Test to verify the actual form submission behavior
"""

import requests
from bs4 import BeautifulSoup

def test_form_submission():
    """Test the actual form submission behavior"""
    base_url = "http://localhost:5001"
    
    login_data = {
        'username': 'testfirstuser',
        'password': 'testpass123'
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
        
        # Get the transactions page
        print("\n2. Getting transactions page...")
        response = session.get(f"{base_url}/transactions")
        if response.status_code != 200:
            print(f"✗ Failed to get transactions page: {response.status_code}")
            return False
        
        # Parse the HTML to get form details
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')
        if not form:
            print("✗ No form found on page")
            return False
        
        print(f"Form method: {form.get('method', 'GET')}")
        print(f"Form action: {form.get('action', 'current page')}")
        
        # Get all account checkboxes
        account_checkboxes = soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        print(f"Found {len(account_checkboxes)} account checkboxes")
        
        if not account_checkboxes:
            print("✗ No account checkboxes found")
            return False
        
        # Test direct GET request with account filter
        print("\n3. Testing direct GET with filter...")
        first_account = account_checkboxes[0]['value']
        test_url = f"{base_url}/transactions?account_id={first_account}"
        
        get_response = session.get(test_url)
        if get_response.status_code != 200:
            print(f"✗ GET request failed: {get_response.status_code}")
            return False
        
        # Check if checkbox is checked in response
        response_soup = BeautifulSoup(get_response.text, 'html.parser')
        checked_checkbox = response_soup.find('input', {
            'name': 'account_id', 
            'value': first_account, 
            'checked': True
        })
        
        if checked_checkbox:
            print(f"✓ Account {first_account[:8]}... checkbox IS preserved with direct GET")
        else:
            print(f"✗ Account {first_account[:8]}... checkbox is NOT preserved with direct GET")
            
            # Debug: show all checkboxes in response
            response_checkboxes = response_soup.find_all('input', {'name': 'account_id'})
            print("Debug - All account checkboxes in response:")
            for cb in response_checkboxes:
                checked = "checked" if cb.get('checked') else "unchecked"
                print(f"  {cb['value'][:8]}... - {checked}")
        
        # Check what current_account_ids contains in the template
        print("\n4. Checking current_account_ids in template...")
        current_account_pattern = r"current_account_ids.*?=.*?(\[.*?\])"
        import re
        match = re.search(current_account_pattern, get_response.text, re.DOTALL)
        if match:
            print(f"current_account_ids in template: {match.group(1)}")
        else:
            print("Could not find current_account_ids assignment in template")
            
        # Look for the checkbox render logic
        checkbox_render_pattern = r"account\.id\|string in current_account_ids"
        if re.search(checkbox_render_pattern, get_response.text):
            print("✓ Found checkbox render logic in template")
        else:
            print("✗ Checkbox render logic not found in template")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing form submission behavior")
    print("=" * 50)
    
    test_form_submission()
