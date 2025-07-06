#!/usr/bin/env python3
"""
Simple test to debug checkbox state preservation
"""

import requests
import re

def debug_checkbox_preservation():
    """Debug checkbox state preservation in detail"""
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
        
        # Test 1: Get initial page
        print("\n2. Loading initial transactions page...")
        initial_response = session.get(f"{base_url}/transactions")
        initial_content = initial_response.text
        
        # Extract all account IDs from initial page
        account_pattern = r'name="account_id" value="([^"]+)"'
        accounts = re.findall(account_pattern, initial_content)
        print(f"Found accounts: {[acc[:8] + '...' for acc in accounts[:3]]} (showing first 3)")
        
        if not accounts:
            print("✗ No accounts found")
            return False
        
        # Test 2: Filter with first account
        print(f"\n3. Testing filter with account: {accounts[0][:8]}...")
        filter_url = f"{base_url}/transactions?account_id={accounts[0]}"
        print(f"Filter URL: {filter_url}")
        
        filter_response = session.get(filter_url)
        filter_content = filter_response.text
        
        print(f"Response status: {filter_response.status_code}")
        
        # Debug: Look for current_account_ids in the template context
        print("\n4. Debugging template variables...")
        
        # Look for how current_account_ids is passed to template
        current_ids_pattern = r"current_account_ids['\"]?\s*:\s*(\[.*?\])"
        match = re.search(current_ids_pattern, filter_content, re.DOTALL)
        if match:
            print(f"Found current_account_ids in template context: {match.group(1)}")
        else:
            print("current_account_ids not found in template context")
        
        # Look for the specific checkbox for our filtered account
        checkbox_context_pattern = rf'value="{re.escape(accounts[0])}"[^>]*>'
        match = re.search(checkbox_context_pattern, filter_content)
        if match:
            # Get surrounding context
            start = max(0, match.start() - 100)
            end = min(len(filter_content), match.end() + 100)
            context = filter_content[start:end]
            print(f"\nCheckbox context for {accounts[0][:8]}...:")
            print("-" * 60)
            print(context)
            print("-" * 60)
            
            if 'checked' in context:
                print("✓ 'checked' attribute found in context")
            else:
                print("✗ 'checked' attribute NOT found in context")
        else:
            print(f"✗ Checkbox for account {accounts[0][:8]}... not found in response")
        
        # Test 3: Check what the backend is actually sending
        print("\n5. Debugging backend response...")
        
        # Look for template render call
        render_pattern = r"render_template.*current_account_ids.*?=(.*?),"
        # This won't work in the response, let me check the actual checkbox rendering
        
        # Look for all checkboxes with checked attribute
        checked_pattern = r'name="account_id"[^>]*checked[^>]*value="([^"]+)"'
        checked_accounts = re.findall(checked_pattern, filter_content)
        
        if checked_accounts:
            print(f"Accounts with checked checkboxes: {[acc[:8] + '...' for acc in checked_accounts]}")
            if accounts[0] in checked_accounts:
                print(f"✓ Target account {accounts[0][:8]}... is in checked list")
            else:
                print(f"✗ Target account {accounts[0][:8]}... is NOT in checked list")
        else:
            print("No accounts have checked checkboxes")
        
        # Test 4: Check the template logic directly
        print("\n6. Checking template logic...")
        template_logic_pattern = r'{% if account\.id\|string in current_account_ids %}checked{% endif %}'
        if re.search(template_logic_pattern, filter_content):
            print("✓ Template checkbox logic found")
        else:
            print("✗ Template checkbox logic not found")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Debugging checkbox state preservation")
    print("=" * 50)
    
    debug_checkbox_preservation()
