#!/usr/bin/env python3
"""
Debug the specific Mercury Checking ••3295 account issue
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_specific_account_issue():
    """Debug the specific Mercury Checking ••3295 account issue"""
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
        print("\n2. Analyzing all accounts and transactions...")
        initial_response = session.get(f"{base_url}/transactions")
        initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        # Get all account checkboxes and their labels
        account_checkboxes = initial_soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        
        print(f"✓ Found {len(account_checkboxes)} accounts:")
        account_info = {}
        
        for checkbox in account_checkboxes:
            account_id = checkbox.get('value')
            label = checkbox.find_next('label')
            account_name = label.get_text(strip=True) if label else "Unknown"
            account_info[account_id] = account_name
            print(f"  - {account_name} → {account_id}")
            
            # Check if this is the problematic account
            if "3295" in account_name:
                print(f"    *** FOUND PROBLEMATIC ACCOUNT: {account_name} → {account_id}")
        
        # Look for any mention of "3295" in the transaction rows
        print(f"\n3. Searching for '3295' in transaction content...")
        transaction_rows = initial_soup.find_all('tr')[1:]  # Skip header
        
        found_3295_rows = []
        for i, row in enumerate(transaction_rows):
            cells = row.find_all('td')
            if cells:
                row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                if "3295" in row_text:
                    found_3295_rows.append((i+1, row_text))
                    print(f"  Row {i+1}: {row_text}")
        
        if not found_3295_rows:
            print("  ✗ No transactions found containing '3295'")
        else:
            print(f"  ✓ Found {len(found_3295_rows)} transaction(s) containing '3295'")
        
        # Let's check what happens when we access the page with no filters vs with filters
        print(f"\n4. Testing page states...")
        
        # Test 1: No filters (what you see when you "remove filter")
        print("  Testing: No filters")
        no_filter_response = session.get(f"{base_url}/transactions")
        no_filter_soup = BeautifulSoup(no_filter_response.text, 'html.parser')
        no_filter_rows = no_filter_soup.find_all('tr')[1:]
        no_filter_count = len([row for row in no_filter_rows if row.find('td')])
        print(f"    → Transactions shown: {no_filter_count}")
        
        # Check for 3295 in no-filter state
        no_filter_3295 = []
        for row in no_filter_rows:
            cells = row.find_all('td')
            if cells:
                row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                if "3295" in row_text:
                    no_filter_3295.append(row_text[:100])
        
        if no_filter_3295:
            print(f"    ✓ Found {len(no_filter_3295)} transactions with '3295' in no-filter state")
            for txt in no_filter_3295:
                print(f"      → {txt}...")
        else:
            print(f"    ✗ No '3295' transactions in no-filter state")
        
        # Test 2: Filter by first account
        if account_checkboxes:
            first_account_id = account_checkboxes[0].get('value')
            first_account_name = account_info.get(first_account_id, "Unknown")
            
            print(f"  Testing: Filter by {first_account_name}")
            filter_response = session.get(f"{base_url}/transactions?account_id={first_account_id}")
            filter_soup = BeautifulSoup(filter_response.text, 'html.parser')
            filter_rows = filter_soup.find_all('tr')[1:]
            filter_count = len([row for row in filter_rows if row.find('td')])
            print(f"    → Transactions shown: {filter_count}")
            
            # Check for 3295 in filtered state
            filter_3295 = []
            for row in filter_rows:
                cells = row.find_all('td')
                if cells:
                    row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                    if "3295" in row_text:
                        filter_3295.append(row_text[:100])
            
            if filter_3295:
                print(f"    ⚠️  Found {len(filter_3295)} transactions with '3295' in filtered state (THIS SHOULD NOT HAPPEN)")
                for txt in filter_3295:
                    print(f"      → {txt}...")
            else:
                print(f"    ✓ No '3295' transactions in filtered state (this is correct)")
        
        print(f"\n5. Summary of findings:")
        print(f"  - Total accounts available: {len(account_checkboxes)}")
        print(f"  - Transactions without filter: {no_filter_count}")
        print(f"  - Transactions containing '3295': {len(found_3295_rows)}")
        print(f"  - '3295' transactions in no-filter state: {len(no_filter_3295)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Debugging specific Mercury Checking ••3295 account issue")
    print("=" * 70)
    debug_specific_account_issue()
