#!/usr/bin/env python3
"""
Debug the specific filtering issues described by the user
"""

import requests
import re

def debug_filtering_issues():
    """Debug the specific issues: wrong account selected, filters not clearing"""
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
        
        # Get initial page - check what accounts are available and their order
        print("\n2. Checking initial page state...")
        initial_response = session.get(f"{base_url}/transactions")
        initial_content = initial_response.text
        
        # Find all accounts in order they appear
        account_pattern = r'<input[^>]*name="account_id"[^>]*value="([^"]+)"[^>]*>.*?<label[^>]*>([^<]+)</label>'
        accounts_with_names = re.findall(account_pattern, initial_content, re.DOTALL)
        
        print("Available accounts in order:")
        for i, (account_id, account_name) in enumerate(accounts_with_names):
            print(f"  {i+1}. {account_id[:8]}... - {account_name.strip()}")
        
        if not accounts_with_names:
            print("✗ No accounts found!")
            return False
        
        # Check if any accounts are already selected on initial load
        checked_accounts = []
        for account_id, account_name in accounts_with_names:
            checkbox_pattern = rf'value="{re.escape(account_id)}"[^>]*checked'
            if re.search(checkbox_pattern, initial_content):
                checked_accounts.append((account_id, account_name))
        
        if checked_accounts:
            print(f"\nInitial state has {len(checked_accounts)} accounts pre-selected:")
            for account_id, account_name in checked_accounts:
                print(f"  - {account_id[:8]}... - {account_name.strip()}")
        else:
            print("\nInitial state: No accounts pre-selected")
        
        # Test 1: Filter by first account
        print(f"\n3. Testing filter by first account...")
        first_account_id, first_account_name = accounts_with_names[0]
        print(f"Selecting account: {first_account_id[:8]}... - {first_account_name.strip()}")
        
        filter_url = f"{base_url}/transactions?account_id={first_account_id}"
        print(f"Filter URL: {filter_url}")
        
        filter_response = session.get(filter_url)
        filter_content = filter_response.text
        
        # Check which accounts are now selected
        selected_after_filter = []
        for account_id, account_name in accounts_with_names:
            checkbox_pattern = rf'value="{re.escape(account_id)}"[^>]*checked'
            if re.search(checkbox_pattern, filter_content):
                selected_after_filter.append((account_id, account_name))
        
        print("After filtering, selected accounts:")
        if selected_after_filter:
            for account_id, account_name in selected_after_filter:
                print(f"  ✓ {account_id[:8]}... - {account_name.strip()}")
                if account_id == first_account_id:
                    print("    ^ This is the account we wanted to select ✓")
                else:
                    print("    ^ This is NOT the account we wanted to select ✗")
        else:
            print("  No accounts selected after filtering ✗")
        
        # Check transaction count
        transaction_pattern = r'class="[^"]*transaction[^"]*"'
        transaction_count = len(re.findall(transaction_pattern, filter_content))
        print(f"Transactions displayed: {transaction_count}")
        
        # Test 2: Clear filters
        print(f"\n4. Testing clear filters...")
        clear_url = f"{base_url}/transactions"
        print(f"Clear URL: {clear_url}")
        
        clear_response = session.get(clear_url)
        clear_content = clear_response.text
        
        # Check which accounts are selected after clearing
        selected_after_clear = []
        for account_id, account_name in accounts_with_names:
            checkbox_pattern = rf'value="{re.escape(account_id)}"[^>]*checked'
            if re.search(checkbox_pattern, clear_content):
                selected_after_clear.append((account_id, account_name))
        
        print("After clearing filters, selected accounts:")
        if selected_after_clear:
            for account_id, account_name in selected_after_clear:
                print(f"  ✓ {account_id[:8]}... - {account_name.strip()}")
            print("  ^ Filters were NOT properly cleared ✗")
        else:
            print("  No accounts selected - filters properly cleared ✓")
        
        # Check transaction count after clearing
        transaction_count_after_clear = len(re.findall(transaction_pattern, clear_content))
        print(f"Transactions displayed after clear: {transaction_count_after_clear}")
        
        # Test 3: Check default behavior and user settings
        print(f"\n5. Investigating default behavior...")
        
        # Look at what the backend is sending for current_account_ids
        current_ids_debug = re.search(r'current_account_ids["\']?\s*[:\[]([^}\]]*)', clear_content)
        if current_ids_debug:
            print(f"Backend current_account_ids: {current_ids_debug.group(1)}")
        
        # Check if there's a primary account setting
        print("\n6. Checking user settings...")
        user_check_url = f"{base_url}/api/user/settings" if "/api/user/settings" in clear_content else None
        if user_check_url:
            settings_response = session.get(user_check_url)
            print(f"User settings response: {settings_response.status_code}")
        else:
            print("No user settings API endpoint found")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Debugging specific filtering issues")
    print("=" * 50)
    
    debug_filtering_issues()
