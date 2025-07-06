#!/usr/bin/env python3
"""
Test to reproduce the specific account filtering bug
"""

import requests
import re

def test_specific_account_bug():
    """Test the specific bug where filtering to one account shows transactions from another"""
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
        
        # Get initial page to see all accounts
        print("\n2. Loading transactions page...")
        initial_response = session.get(f"{base_url}/transactions")
        initial_content = initial_response.text
        
        # Find Mercury Savings ••1996 account ID
        savings_1996_pattern = r'value="([^"]+)"[^>]*>[^<]*Mercury Savings[^<]*1996'
        savings_match = re.search(savings_1996_pattern, initial_content)
        
        if not savings_match:
            print("✗ Could not find Mercury Savings ••1996 account")
            # Let's see what accounts are available
            print("Available accounts:")
            account_pattern = r'value="([^"]+)"[^>]*>\s*<label[^>]*>([^<]+)</label>'
            accounts = re.findall(account_pattern, initial_content)
            for account_id, name in accounts:
                print(f"  {account_id[:8]}... = {name.strip()}")
            return False
        
        savings_1996_id = savings_match.group(1)
        print(f"✓ Found Mercury Savings ••1996: {savings_1996_id[:8]}...")
        
        # Filter to Mercury Savings ••1996
        print(f"\n3. Filtering to Mercury Savings ••1996 ({savings_1996_id[:8]}...)...")
        filter_url = f"{base_url}/transactions?account_id={savings_1996_id}"
        print(f"Filter URL: {filter_url}")
        
        filter_response = session.get(filter_url)
        filter_content = filter_response.text
        
        # Check what account is actually selected in the checkbox
        print("\n4. Checking which accounts are selected after filtering...")
        checked_pattern = r'<input[^>]*name="account_id"[^>]*checked[^>]*value="([^"]+)"'
        checked_accounts = re.findall(checked_pattern, filter_content)
        
        if checked_accounts:
            for checked_id in checked_accounts:
                print(f"✓ Checked account: {checked_id[:8]}...")
                if checked_id == savings_1996_id:
                    print("  ✓ This is the correct account (Mercury Savings ••1996)")
                else:
                    print("  ✗ This is NOT the correct account!")
        else:
            print("✗ No accounts are checked after filtering")
        
        # Check what transactions are actually displayed
        print("\n5. Checking what transactions are displayed...")
        
        # Look for transaction cards or table rows
        # First try to find transaction data
        transaction_pattern = r'data-account-name="([^"]*)"'
        transaction_accounts = re.findall(transaction_pattern, filter_content)
        
        if transaction_accounts:
            print("Transactions shown are from accounts:")
            for account_name in set(transaction_accounts):
                print(f"  - {account_name}")
                
            # Check if any transactions are from Mercury Checking ••3295
            checking_3295_transactions = [acc for acc in transaction_accounts if "3295" in acc]
            if checking_3295_transactions:
                print("✗ BUG CONFIRMED: Found transactions from Mercury Checking ••3295")
                print(f"   Count: {len(checking_3295_transactions)} transactions")
            else:
                print("✓ No incorrect transactions found")
        else:
            # Try alternative pattern
            print("No transactions found with data-account-name, trying alternative...")
            
            # Look for account names in the transaction display
            lines = filter_content.split('\n')
            account_names_in_content = []
            for line in lines:
                if 'Mercury' in line and ('Checking' in line or 'Savings' in line):
                    # Extract account name
                    if '••' in line:
                        account_names_in_content.append(line.strip())
            
            if account_names_in_content:
                print("Found account names in content:")
                for name in set(account_names_in_content):
                    print(f"  - {name}")
            else:
                print("No Mercury account names found in transaction content")
        
        # Debug: Let's also check the backend query logic
        print("\n6. Debugging backend logic...")
        
        # Check the actual SQL query being built (we can infer from results)
        print(f"Filter request was for account_id: {savings_1996_id[:8]}...")
        
        # Look for signs of incorrect filtering
        if checked_accounts and checked_accounts[0] != savings_1996_id:
            print(f"✗ PROBLEM: Backend selected {checked_accounts[0][:8]}... instead of {savings_1996_id[:8]}...")
            print("This suggests an issue in the backend account filtering logic")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_account_mapping():
    """Get the mapping of account IDs to names for debugging"""
    base_url = "http://localhost:5001"
    
    login_data = {
        'username': 'testfirstuser',
        'password': 'testpass123'
    }
    
    session = requests.Session()
    
    try:
        # Login
        login_response = session.post(f"{base_url}/login", data=login_data)
        if "dashboard" not in login_response.url:
            return {}
        
        # Get accounts
        response = session.get(f"{base_url}/transactions")
        content = response.text
        
        # Extract account ID to name mapping
        account_mapping = {}
        
        # Find all account checkboxes with their labels
        checkbox_pattern = r'<input[^>]*name="account_id"[^>]*value="([^"]+)"[^>]*id="account_[^"]*"[^>]*>\s*<label[^>]*>([^<]+)</label>'
        matches = re.findall(checkbox_pattern, content, re.DOTALL)
        
        for account_id, account_name in matches:
            account_mapping[account_id] = account_name.strip()
        
        return account_mapping
        
    except Exception:
        return {}

if __name__ == "__main__":
    print("Testing specific account filtering bug")
    print("=" * 60)
    
    # First get account mapping
    print("Getting account mapping...")
    mapping = get_account_mapping()
    if mapping:
        print("Account ID -> Name mapping:")
        for account_id, name in mapping.items():
            print(f"  {account_id[:8]}... -> {name}")
    
    print("\n" + "=" * 60)
    
    # Test the specific bug
    test_specific_account_bug()
