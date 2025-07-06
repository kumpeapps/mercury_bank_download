#!/usr/bin/env python3
"""
Debug database content and filtering queries directly
"""

import requests
from bs4 import BeautifulSoup

def debug_database_content():
    """Check what's actually in the database and how filtering works"""
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
        
        # Get initial transactions page and count transactions
        print("\n2. Checking unfiltered transactions...")
        initial_response = session.get(f"{base_url}/transactions")
        initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        # Count transaction rows
        transaction_rows = initial_soup.find_all('tr')[1:]  # Skip header
        transaction_count = len([row for row in transaction_rows if row.find('td')])
        print(f"✓ Total transactions without filter: {transaction_count}")
        
        # Get account information
        account_checkboxes = initial_soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        print(f"✓ Available accounts in form: {len(account_checkboxes)}")
        
        # Let's also look at the actual transaction data in the table
        print("\n3. Analyzing transaction table content...")
        for i, row in enumerate(transaction_rows[:5]):  # Check first 5 rows
            cells = row.find_all('td')
            if cells and len(cells) > 1:
                # Try to find account info in the row
                row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                print(f"  Row {i+1}: {row_text[:100]}...")
        
        # Test filtering with each account
        print(f"\n4. Testing filter with each available account...")
        for i, checkbox in enumerate(account_checkboxes[:3]):  # Test first 3 accounts
            account_id = checkbox.get('value')
            
            # Find account name
            label = checkbox.find_next('label')
            account_name = label.get_text(strip=True) if label else f"Account {i+1}"
            
            print(f"\n  Testing account: {account_name} ({account_id[:8]}...)")
            
            # Apply filter
            filter_url = f"{base_url}/transactions?account_id={account_id}"
            filter_response = session.get(filter_url)
            
            if filter_response.status_code != 200:
                print(f"    ✗ Filter request failed: {filter_response.status_code}")
                continue
            
            filter_soup = BeautifulSoup(filter_response.text, 'html.parser')
            filtered_rows = filter_soup.find_all('tr')[1:]  # Skip header
            filtered_count = len([row for row in filtered_rows if row.find('td')])
            
            print(f"    → Filtered transactions: {filtered_count}")
            
            # Check if the checkbox is checked
            checked_checkbox = filter_soup.find('input', {'name': 'account_id', 'value': account_id, 'checked': True})
            if checked_checkbox:
                print(f"    ✓ Checkbox is checked after filtering")
            else:
                print(f"    ✗ Checkbox is NOT checked after filtering")
        
        # Test clearing filter
        print(f"\n5. Testing filter clearing...")
        clear_response = session.get(f"{base_url}/transactions")
        clear_soup = BeautifulSoup(clear_response.text, 'html.parser')
        clear_rows = clear_soup.find_all('tr')[1:]  # Skip header
        clear_count = len([row for row in clear_rows if row.find('td')])
        
        print(f"✓ Transactions after clearing filter: {clear_count}")
        
        # Check for any checked checkboxes after clearing
        checked_after_clear = clear_soup.find_all('input', {'name': 'account_id', 'checked': True})
        if checked_after_clear:
            print(f"✗ {len(checked_after_clear)} checkboxes still checked after clearing")
            for cb in checked_after_clear:
                label = cb.find_next('label')
                name = label.get_text(strip=True) if label else "Unknown"
                print(f"    - {name} ({cb.get('value')[:8]}...)")
        else:
            print(f"✓ No checkboxes checked after clearing")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Debugging database content and filtering behavior")
    print("=" * 60)
    debug_database_content()
