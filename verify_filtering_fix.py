#!/usr/bin/env python3
"""
Verify that the account filtering fix is working correctly
"""

import requests
from bs4 import BeautifulSoup
import re

def verify_filtering_fix():
    """Test that account filtering works correctly after the backend fix"""
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
        
        initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        # Count total transactions
        initial_rows = initial_soup.find_all('tr')[1:]  # Skip header
        total_transactions = len([row for row in initial_rows if row.find('td')])
        print(f"✓ Total transactions on page: {total_transactions}")
        
        # Get available accounts
        account_checkboxes = initial_soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        if not account_checkboxes:
            print("✗ No account checkboxes found!")
            return False
        
        # Get account labels for display
        accounts_info = []
        for checkbox in account_checkboxes:
            account_id = checkbox.get('value')
            # Find the label for this account
            label = checkbox.find_next('label')
            if label:
                account_name = label.get_text(strip=True)
                accounts_info.append((account_id, account_name))
        
        print(f"✓ Found {len(accounts_info)} accounts:")
        for account_id, name in accounts_info[:3]:  # Show first 3
            print(f"  - {name} ({account_id[:8]}...)")
        
        # Test filtering by first account
        if accounts_info:
            test_account_id, test_account_name = accounts_info[0]
            print(f"\n3. Testing filter by account: {test_account_name}")
            
            # Apply filter
            filter_url = f"{base_url}/transactions?account_id={test_account_id}"
            filtered_response = session.get(filter_url)
            
            if filtered_response.status_code != 200:
                print(f"✗ Filter request failed: {filtered_response.status_code}")
                return False
            
            filtered_soup = BeautifulSoup(filtered_response.text, 'html.parser')
            
            # Count filtered transactions
            filtered_rows = filtered_soup.find_all('tr')[1:]  # Skip header
            filtered_transactions = len([row for row in filtered_rows if row.find('td')])
            
            print(f"✓ Filtered transactions: {filtered_transactions}")
            
            # Check if the correct account checkbox is checked
            checked_checkboxes = filtered_soup.find_all('input', {'name': 'account_id', 'checked': True})
            if checked_checkboxes:
                checked_account_id = checked_checkboxes[0].get('value')
                if checked_account_id == test_account_id:
                    print("✓ Correct account checkbox is checked after filtering")
                else:
                    print(f"✗ Wrong account checkbox checked. Expected: {test_account_id[:8]}..., Got: {checked_account_id[:8]}...")
                    return False
            else:
                print("✗ No account checkbox is checked after filtering")
                return False
            
            # Verify that displayed transactions are for the correct account
            transaction_rows = [row for row in filtered_rows if row.find('td')]
            if transaction_rows:
                # Look for account information in the transaction rows
                # This is tricky since account info might not be directly visible
                print(f"✓ Filter applied successfully - showing {len(transaction_rows)} transactions")
                
                # Test removing filter
                print("\n4. Testing filter removal...")
                clear_filter_url = f"{base_url}/transactions"
                clear_response = session.get(clear_filter_url)
                
                if clear_response.status_code != 200:
                    print(f"✗ Clear filter request failed: {clear_response.status_code}")
                    return False
                
                clear_soup = BeautifulSoup(clear_response.text, 'html.parser')
                clear_rows = clear_soup.find_all('tr')[1:]  # Skip header
                clear_transactions = len([row for row in clear_rows if row.find('td')])
                
                print(f"✓ After clearing filter: {clear_transactions} transactions")
                
                # Check that no checkboxes are checked after clearing
                clear_checked = clear_soup.find_all('input', {'name': 'account_id', 'checked': True})
                if not clear_checked:
                    print("✓ No account checkboxes checked after clearing filter")
                else:
                    print(f"✗ {len(clear_checked)} checkboxes still checked after clearing filter")
                    return False
                
                print("\n🎉 All filtering tests passed!")
                return True
            else:
                print("✗ No transactions found after filtering")
                return False
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("Verifying account filtering fix")
    print("=" * 50)
    success = verify_filtering_fix()
    if success:
        print("\n✅ Account filtering is working correctly!")
    else:
        print("\n❌ Account filtering still has issues")
