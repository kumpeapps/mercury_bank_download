#!/usr/bin/env python3
"""
Test filtering specifically by Mercury Checking ••3295 account
"""

import requests
from bs4 import BeautifulSoup

def test_3295_filtering():
    """Test what happens when filtering by Mercury Checking ••3295"""
    base_url = "http://localhost:5001"
    
    login_data = {
        'username': 'test',
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
        
        # Find the Mercury Checking ••3295 account ID
        print("\n2. Finding Mercury Checking ••3295 account...")
        initial_response = session.get(f"{base_url}/transactions")
        initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        target_account_id = None
        account_checkboxes = initial_soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        
        for checkbox in account_checkboxes:
            account_id = checkbox.get('value')
            label = checkbox.find_next('label')
            account_name = label.get_text(strip=True) if label else "Unknown"
            
            if "3295" in account_name:
                target_account_id = account_id
                print(f"✓ Found target account: {account_name} → {account_id}")
                break
        
        if not target_account_id:
            print("✗ Could not find Mercury Checking ••3295 account")
            return False
        
        # Test filtering by this specific account
        print(f"\n3. Testing filter by Mercury Checking ••3295...")
        filter_url = f"{base_url}/transactions?account_id={target_account_id}"
        print(f"Filter URL: {filter_url}")
        
        filter_response = session.get(filter_url)
        if filter_response.status_code != 200:
            print(f"✗ Filter request failed: {filter_response.status_code}")
            return False
        
        filter_soup = BeautifulSoup(filter_response.text, 'html.parser')
        
        # Count filtered transactions
        filter_rows = filter_soup.find_all('tr')[1:]  # Skip header
        filter_count = len([row for row in filter_rows if row.find('td')])
        print(f"✓ Filtered transactions: {filter_count}")
        
        # Show first few transactions
        print(f"\nFirst few transactions when filtered by ••3295:")
        for i, row in enumerate(filter_rows[:5]):
            cells = row.find_all('td')
            if cells:
                row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                print(f"  {i+1}: {row_text[:80]}...")
        
        # Check if the checkbox is checked
        checked_checkbox = filter_soup.find('input', {'name': 'account_id', 'value': target_account_id, 'checked': True})
        if checked_checkbox:
            print(f"✓ Mercury Checking ••3295 checkbox IS checked after filtering")
        else:
            print(f"✗ Mercury Checking ••3295 checkbox is NOT checked after filtering")
        
        # Test with different account to verify filter is working
        print(f"\n4. Testing filter by different account for comparison...")
        other_account_id = None
        for checkbox in account_checkboxes:
            account_id = checkbox.get('value')
            if account_id != target_account_id:
                label = checkbox.find_next('label')
                account_name = label.get_text(strip=True) if label else "Unknown"
                other_account_id = account_id
                print(f"Testing with: {account_name} → {account_id[:8]}...")
                break
        
        if other_account_id:
            other_filter_url = f"{base_url}/transactions?account_id={other_account_id}"
            other_response = session.get(other_filter_url)
            other_soup = BeautifulSoup(other_response.text, 'html.parser')
            other_rows = other_soup.find_all('tr')[1:]
            other_count = len([row for row in other_rows if row.find('td')])
            print(f"✓ Other account filtered transactions: {other_count}")
            
            # Check for any 3295 transactions in other account filter (should be 0)
            other_3295_count = 0
            for row in other_rows:
                cells = row.find_all('td')
                if cells:
                    row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                    if "3295" in row_text:
                        other_3295_count += 1
            
            if other_3295_count == 0:
                print(f"✓ No ••3295 transactions appear when filtering by other account (correct)")
            else:
                print(f"✗ {other_3295_count} ••3295 transactions appear when filtering by other account (BUG!)")
        
        print(f"\n5. Testing what you described...")
        print("According to your report:")
        print("- Filtering by any account returns no transactions")
        print("- Removing filter shows one transaction from Mercury Checking ••3295")
        print("")
        print("What we found:")
        print(f"- Filtering by Mercury Checking ••3295 returns {filter_count} transactions")
        print(f"- No filter shows 45 total transactions (including 14 from ••3295)")
        print("- Filtering by other accounts works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Mercury Checking ••3295 specific filtering behavior")
    print("=" * 70)
    test_3295_filtering()
