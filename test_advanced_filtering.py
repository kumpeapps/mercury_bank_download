#!/usr/bin/env python3
"""
Test multiple account and status filtering scenarios
"""

import requests
from bs4 import BeautifulSoup

def test_advanced_filtering():
    """Test multiple filtering scenarios"""
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
        
        # Get initial page and account info
        initial_response = session.get(f"{base_url}/transactions")
        initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        account_checkboxes = initial_soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        if len(account_checkboxes) < 2:
            print("✗ Need at least 2 accounts for multi-account test")
            return False
        
        account_ids = [cb.get('value') for cb in account_checkboxes[:2]]
        
        print(f"\n2. Testing multiple account filter...")
        # Test filtering with multiple accounts
        multi_account_url = f"{base_url}/transactions?" + "&".join([f"account_id={aid}" for aid in account_ids])
        multi_response = session.get(multi_account_url)
        
        if multi_response.status_code != 200:
            print(f"✗ Multi-account filter failed: {multi_response.status_code}")
            return False
        
        multi_soup = BeautifulSoup(multi_response.text, 'html.parser')
        checked_checkboxes = multi_soup.find_all('input', {'name': 'account_id', 'checked': True})
        
        if len(checked_checkboxes) == 2:
            print("✓ Multiple account checkboxes correctly checked")
        else:
            print(f"✗ Expected 2 checked accounts, got {len(checked_checkboxes)}")
            return False
        
        print(f"\n3. Testing status filtering...")
        # Test status filtering
        status_url = f"{base_url}/transactions?status=pending&status=sent"
        status_response = session.get(status_url)
        
        if status_response.status_code != 200:
            print(f"✗ Status filter failed: {status_response.status_code}")
            return False
        
        status_soup = BeautifulSoup(status_response.text, 'html.parser')
        checked_status_boxes = status_soup.find_all('input', {'name': 'status', 'checked': True})
        
        if len(checked_status_boxes) >= 1:
            print("✓ Status checkboxes correctly checked")
        else:
            print("✗ No status checkboxes checked")
            return False
        
        print(f"\n4. Testing combined account and status filtering...")
        # Test combined filtering
        combined_url = f"{base_url}/transactions?account_id={account_ids[0]}&status=pending"
        combined_response = session.get(combined_url)
        
        if combined_response.status_code != 200:
            print(f"✗ Combined filter failed: {combined_response.status_code}")
            return False
        
        combined_soup = BeautifulSoup(combined_response.text, 'html.parser')
        checked_accounts = combined_soup.find_all('input', {'name': 'account_id', 'checked': True})
        checked_statuses = combined_soup.find_all('input', {'name': 'status', 'checked': True})
        
        if len(checked_accounts) == 1 and len(checked_statuses) >= 1:
            print("✓ Combined filtering correctly preserves both account and status selections")
        else:
            print(f"✗ Combined filter issue: {len(checked_accounts)} accounts, {len(checked_statuses)} statuses")
            return False
        
        print("\n🎉 All advanced filtering tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("Testing advanced filtering scenarios")
    print("=" * 50)
    success = test_advanced_filtering()
    if success:
        print("\n✅ Advanced filtering is working correctly!")
    else:
        print("\n❌ Advanced filtering has issues")
