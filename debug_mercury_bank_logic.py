#!/usr/bin/env python3
"""
Debug the Mercury account vs Bank account filtering logic
"""

import requests
from bs4 import BeautifulSoup

def debug_mercury_account_logic():
    """Debug the relationship between Mercury accounts and bank accounts"""
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
        print("\n2. Analyzing Mercury account and bank account relationship...")
        initial_response = session.get(f"{base_url}/transactions")
        initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        # Get Mercury account dropdown options
        mercury_select = initial_soup.find('select', {'name': 'mercury_account_id'})
        mercury_options = mercury_select.find_all('option') if mercury_select else []
        
        print("Available Mercury accounts:")
        mercury_accounts = []
        for option in mercury_options:
            value = option.get('value')
            text = option.get_text(strip=True)
            if value:  # Skip the "All Mercury Accounts" option
                mercury_accounts.append((value, text))
                print(f"  - {text} (ID: {value})")
        
        # Get bank account checkboxes
        bank_checkboxes = initial_soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        print(f"\nAvailable bank accounts ({len(bank_checkboxes)} total):")
        bank_accounts = []
        for checkbox in bank_checkboxes:
            account_id = checkbox.get('value')
            label = checkbox.find_next('label')
            account_name = label.get_text(strip=True) if label else "Unknown"
            bank_accounts.append((account_id, account_name))
            print(f"  - {account_name} (ID: {account_id[:8]}...)")
        
        # Test scenario 1: Filter by specific Mercury account + specific bank account
        if mercury_accounts and bank_accounts:
            print(f"\n3. Testing Mercury account + bank account filtering...")
            
            # Test with first Mercury account and first bank account
            mercury_id, mercury_name = mercury_accounts[0]
            bank_id, bank_name = bank_accounts[0]
            
            print(f"Testing: Mercury account '{mercury_name}' + Bank account '{bank_name}'")
            
            # This is what happens when user selects both filters
            combined_url = f"{base_url}/transactions?mercury_account_id={mercury_id}&account_id={bank_id}"
            print(f"URL: {combined_url}")
            
            combined_response = session.get(combined_url)
            if combined_response.status_code != 200:
                print(f"✗ Request failed: {combined_response.status_code}")
                return False
            
            combined_soup = BeautifulSoup(combined_response.text, 'html.parser')
            combined_rows = combined_soup.find_all('tr')[1:]  # Skip header
            combined_count = len([row for row in combined_rows if row.find('td')])
            
            print(f"Result: {combined_count} transactions")
            
            if combined_count == 0:
                print("⚠️  ZERO RESULTS - This confirms the bug!")
                print("The bank account probably doesn't belong to the selected Mercury account")
            
        # Test scenario 2: Filter by bank account only (no Mercury account selection)
        if bank_accounts:
            print(f"\n4. Testing bank account filtering only...")
            bank_id, bank_name = bank_accounts[0]
            
            print(f"Testing: Only bank account '{bank_name}' (no Mercury account filter)")
            bank_only_url = f"{base_url}/transactions?account_id={bank_id}"
            print(f"URL: {bank_only_url}")
            
            bank_only_response = session.get(bank_only_url)
            bank_only_soup = BeautifulSoup(bank_only_response.text, 'html.parser')
            bank_only_rows = bank_only_soup.find_all('tr')[1:]
            bank_only_count = len([row for row in bank_only_rows if row.find('td')])
            
            print(f"Result: {bank_only_count} transactions")
            
            if bank_only_count > 0:
                print("✓ Bank account filtering works when no Mercury account is selected")
            else:
                print("✗ Bank account filtering fails even without Mercury account selection")
        
        # Test scenario 3: What happens with "All Mercury Accounts" + specific bank account
        if bank_accounts:
            print(f"\n5. Testing 'All Mercury Accounts' + specific bank account...")
            bank_id, bank_name = bank_accounts[0]
            
            print(f"Testing: All Mercury Accounts + Bank account '{bank_name}'")
            all_mercury_url = f"{base_url}/transactions?account_id={bank_id}"  # No mercury_account_id = All
            
            all_mercury_response = session.get(all_mercury_url)
            all_mercury_soup = BeautifulSoup(all_mercury_response.text, 'html.parser')
            all_mercury_rows = all_mercury_soup.find_all('tr')[1:]
            all_mercury_count = len([row for row in all_mercury_rows if row.find('td')])
            
            print(f"Result: {all_mercury_count} transactions")
            
            # Check if Mercury account dropdown shows "All Mercury Accounts" selected
            mercury_select_after = all_mercury_soup.find('select', {'name': 'mercury_account_id'})
            if mercury_select_after:
                selected_option = mercury_select_after.find('option', {'selected': True})
                if selected_option:
                    selected_text = selected_option.get_text(strip=True)
                    print(f"Mercury account dropdown shows: '{selected_text}'")
                else:
                    print("Mercury account dropdown: No option selected")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Debugging Mercury account vs bank account filtering logic")
    print("=" * 70)
    debug_mercury_account_logic()
