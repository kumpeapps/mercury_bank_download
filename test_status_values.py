#!/usr/bin/env python3
"""
Test what status values are being used
"""

import requests
from bs4 import BeautifulSoup

def test_status_values():
    """Test what status values are actually being used"""
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
        
        # Test 1: Load page with no parameters (initial load)
        print("\n2. Testing initial page load (no params)...")
        initial_response = session.get(f"{base_url}/transactions")
        initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        # Check which status checkboxes are checked by default
        status_checkboxes = initial_soup.find_all('input', {'name': 'status', 'type': 'checkbox'})
        print("Status checkboxes on initial load:")
        for checkbox in status_checkboxes:
            status_value = checkbox.get('value')
            is_checked = checkbox.has_attr('checked')
            label = checkbox.find_next('label')
            label_text = label.get_text(strip=True) if label else status_value
            print(f"  {'✓' if is_checked else '○'} {label_text} ({status_value})")
        
        initial_rows = initial_soup.find_all('tr')[1:]
        initial_count = len([row for row in initial_rows if row.find('td')])
        print(f"Transactions shown: {initial_count}")
        
        # Test 2: Explicitly request with no status (should default to posted + pending)
        print("\n3. Testing explicit request with posted + pending...")
        explicit_response = session.get(f"{base_url}/transactions?status=posted&status=pending")
        explicit_soup = BeautifulSoup(explicit_response.text, 'html.parser')
        
        explicit_status_checkboxes = explicit_soup.find_all('input', {'name': 'status', 'type': 'checkbox'})
        print("Status checkboxes with explicit posted + pending:")
        for checkbox in explicit_status_checkboxes:
            status_value = checkbox.get('value')
            is_checked = checkbox.has_attr('checked')
            label = checkbox.find_next('label')
            label_text = label.get_text(strip=True) if label else status_value
            print(f"  {'✓' if is_checked else '○'} {label_text} ({status_value})")
        
        explicit_rows = explicit_soup.find_all('tr')[1:]
        explicit_count = len([row for row in explicit_rows if row.find('td')])
        print(f"Transactions shown: {explicit_count}")
        
        # Test 3: Request with only pending
        print("\n4. Testing with only pending status...")
        pending_response = session.get(f"{base_url}/transactions?status=pending")
        pending_soup = BeautifulSoup(pending_response.text, 'html.parser')
        
        pending_rows = pending_soup.find_all('tr')[1:]
        pending_count = len([row for row in pending_rows if row.find('td')])
        print(f"Transactions shown with only pending: {pending_count}")
        
        # Test 4: Request with only posted/sent
        print("\n5. Testing with only posted status...")
        posted_response = session.get(f"{base_url}/transactions?status=posted")
        posted_soup = BeautifulSoup(posted_response.text, 'html.parser')
        
        posted_rows = posted_soup.find_all('tr')[1:]
        posted_count = len([row for row in posted_rows if row.find('td')])
        print(f"Transactions shown with only posted: {posted_count}")
        
        # Test 5: Request with sent status
        print("\n6. Testing with only sent status...")
        sent_response = session.get(f"{base_url}/transactions?status=sent")
        sent_soup = BeautifulSoup(sent_response.text, 'html.parser')
        
        sent_rows = sent_soup.find_all('tr')[1:]
        sent_count = len([row for row in sent_rows if row.find('td')])
        print(f"Transactions shown with only sent: {sent_count}")
        
        print(f"\n7. Summary:")
        print(f"  Initial load (no params):        {initial_count} transactions")
        print(f"  Explicit posted + pending:       {explicit_count} transactions")
        print(f"  Only pending:                    {pending_count} transactions")
        print(f"  Only posted:                     {posted_count} transactions")
        print(f"  Only sent:                       {sent_count} transactions")
        
        if initial_count != explicit_count:
            print(f"\n⚠️  MISMATCH: Initial load shows different count than explicit posted+pending!")
            print(f"    This suggests the default status logic has a bug.")
        
        if pending_count == 0:
            print(f"\n✓ This explains why filtering returns 0 results!")
            print(f"  When user filters by account, it sends status=pending")
            print(f"  But there are {pending_count} pending transactions in the system")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing status filter values and behavior")
    print("=" * 60)
    test_status_values()
