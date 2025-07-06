#!/usr/bin/env python3
"""
Debug the exact form state and submission behavior
"""

import requests
from bs4 import BeautifulSoup

def debug_form_behavior():
    """Debug what's actually happening with form submission"""
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
        
        # Get initial page and examine default state
        print("\n2. Examining initial page state...")
        initial_response = session.get(f"{base_url}/transactions")
        initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        # Count transactions on initial load
        initial_rows = initial_soup.find_all('tr')[1:]  # Skip header
        initial_count = len([row for row in initial_rows if row.find('td')])
        print(f"✓ Initial transactions shown: {initial_count}")
        
        # Check default status checkboxes
        status_checkboxes = initial_soup.find_all('input', {'name': 'status', 'type': 'checkbox'})
        print(f"\nStatus checkboxes ({len(status_checkboxes)} total):")
        default_statuses = []
        for checkbox in status_checkboxes:
            status_value = checkbox.get('value')
            is_checked = checkbox.has_attr('checked')
            label = checkbox.find_next('label')
            label_text = label.get_text(strip=True) if label else status_value
            status_info = f"{'✓' if is_checked else '○'} {label_text} ({status_value})"
            print(f"  {status_info}")
            if is_checked:
                default_statuses.append(status_value)
        
        print(f"Default checked statuses: {default_statuses}")
        
        # Check account checkboxes default state
        account_checkboxes = initial_soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        checked_accounts = []
        for checkbox in account_checkboxes:
            if checkbox.has_attr('checked'):
                account_id = checkbox.get('value')
                label = checkbox.find_next('label')
                account_name = label.get_text(strip=True) if label else "Unknown"
                checked_accounts.append((account_id, account_name))
        
        if checked_accounts:
            print(f"\nDefault checked accounts:")
            for account_id, account_name in checked_accounts:
                print(f"  ✓ {account_name} ({account_id[:8]}...)")
        else:
            print(f"\nNo accounts checked by default")
        
        # Now simulate what happens when user clicks a checkbox and submits
        print(f"\n3. Simulating user interaction...")
        
        # Get first account for testing
        first_account_checkbox = account_checkboxes[0]
        test_account_id = first_account_checkbox.get('value')
        test_label = first_account_checkbox.find_next('label')
        test_account_name = test_label.get_text(strip=True) if test_label else "Unknown"
        
        print(f"Simulating: User checks '{test_account_name}' and clicks Filter")
        
        # Simulate form submission with this account checked
        form_data = {
            'account_id': test_account_id,  # Single account selected
            'status': default_statuses  # Keep default statuses
        }
        
        print(f"Form data being sent: {form_data}")
        
        # Submit form (GET request with params)
        filter_response = session.get(f"{base_url}/transactions", params=form_data)
        print(f"Request URL: {filter_response.url}")
        
        if filter_response.status_code != 200:
            print(f"✗ Filter request failed: {filter_response.status_code}")
            return False
        
        filter_soup = BeautifulSoup(filter_response.text, 'html.parser')
        filter_rows = filter_soup.find_all('tr')[1:]
        filter_count = len([row for row in filter_rows if row.find('td')])
        
        print(f"✓ Filtered result: {filter_count} transactions")
        
        # Check which checkboxes are checked after filtering
        filtered_account_checkboxes = filter_soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        filtered_checked_accounts = []
        for checkbox in filtered_account_checkboxes:
            if checkbox.has_attr('checked'):
                account_id = checkbox.get('value')
                label = checkbox.find_next('label')
                account_name = label.get_text(strip=True) if label else "Unknown"
                filtered_checked_accounts.append((account_id, account_name))
        
        if filtered_checked_accounts:
            print(f"After filtering, checked accounts:")
            for account_id, account_name in filtered_checked_accounts:
                print(f"  ✓ {account_name} ({account_id[:8]}...)")
                if account_id == test_account_id:
                    print(f"    → Correct! The filtered account is checked")
                else:
                    print(f"    → ERROR! Different account is checked")
        else:
            print(f"✗ No accounts checked after filtering (BUG!)")
        
        # Test the "Clear" button behavior
        print(f"\n4. Testing Clear button...")
        clear_response = session.get(f"{base_url}/transactions")
        clear_soup = BeautifulSoup(clear_response.text, 'html.parser')
        clear_rows = clear_soup.find_all('tr')[1:]
        clear_count = len([row for row in clear_rows if row.find('td')])
        
        print(f"After clicking Clear: {clear_count} transactions")
        
        if clear_count == initial_count:
            print(f"✓ Clear button works correctly")
        elif clear_count == 1:
            print(f"✗ Clear button shows only 1 transaction (this matches your reported bug!)")
            
            # Let's see what that one transaction is
            clear_transaction_rows = [row for row in clear_rows if row.find('td')]
            if clear_transaction_rows:
                first_clear_row = clear_transaction_rows[0]
                cells = first_clear_row.find_all('td')
                if cells:
                    row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                    print(f"    The single transaction: {row_text[:100]}...")
                    if "3295" in row_text:
                        print(f"    → This is indeed from Mercury Checking ••3295!")
        else:
            print(f"⚠️ Clear button shows {clear_count} transactions (unexpected)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Debugging exact form behavior and submission")
    print("=" * 60)
    debug_form_behavior()
