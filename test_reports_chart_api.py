#!/usr/bin/env python3
"""
Test the Reports page chart API endpoints when filtering by account
"""

import requests
from bs4 import BeautifulSoup
import json

def test_reports_chart_apis():
    """Test the chart API endpoints on the Reports page when filtering by account"""
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
            print(f"Response URL: {login_response.url}")
            print(f"Status: {login_response.status_code}")
            return False
        print("✓ Login successful")
        
        # Get the reports page to see available accounts
        print("\n2. Getting Reports page to find available accounts...")
        reports_response = session.get(f"{base_url}/reports")
        if reports_response.status_code != 200:
            print(f"✗ Reports page failed: {reports_response.status_code}")
            return False
        
        reports_soup = BeautifulSoup(reports_response.text, 'html.parser')
        
        # Find bank account checkboxes
        account_checkboxes = reports_soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        print(f"✓ Found {len(account_checkboxes)} bank accounts")
        
        accounts = []
        for checkbox in account_checkboxes:
            account_id = checkbox.get('value')
            label = checkbox.find_next('label')
            account_name = label.get_text(strip=True) if label else "Unknown"
            accounts.append((account_id, account_name))
            print(f"  - {account_name} (ID: {account_id[:8]}...)")
        
        if not accounts:
            print("✗ No accounts found")
            return False
        
        # Test chart APIs without any filters first
        print(f"\n3. Testing chart APIs WITHOUT filters...")
        
        # Test budget chart API
        budget_url = f"{base_url}/api/budget_data?months=12&include_pending=true&show_subcategories=false"
        print(f"Budget API URL: {budget_url}")
        budget_response = session.get(budget_url)
        print(f"Budget API Status: {budget_response.status_code}")
        
        if budget_response.status_code == 200:
            budget_data = budget_response.json()
            print(f"Budget API Response: labels={len(budget_data.get('labels', []))}, datasets={len(budget_data.get('datasets', []))}")
        else:
            print(f"Budget API Error: {budget_response.text}")
        
        # Test expense chart API
        expense_url = f"{base_url}/api/expense_breakdown?months=3&include_pending=true&show_subcategories=false"
        print(f"Expense API URL: {expense_url}")
        expense_response = session.get(expense_url)
        print(f"Expense API Status: {expense_response.status_code}")
        
        if expense_response.status_code == 200:
            expense_data = expense_response.json()
            print(f"Expense API Response: labels={len(expense_data.get('labels', []))}, datasets={len(expense_data.get('datasets', []))}")
        else:
            print(f"Expense API Error: {expense_response.text}")
        
        # Now test with account filtering
        print(f"\n4. Testing chart APIs WITH account filtering...")
        
        for i, (account_id, account_name) in enumerate(accounts[:3]):  # Test first 3 accounts
            print(f"\n--- Testing with account: {account_name} ---")
            
            # Test budget chart API with account filter
            budget_filtered_url = f"{base_url}/api/budget_data?months=12&include_pending=true&show_subcategories=false&account_ids={account_id}"
            print(f"Budget API URL: {budget_filtered_url}")
            budget_filtered_response = session.get(budget_filtered_url)
            print(f"Budget API Status: {budget_filtered_response.status_code}")
            
            if budget_filtered_response.status_code == 200:
                budget_filtered_data = budget_filtered_response.json()
                budget_labels = budget_filtered_data.get('labels', [])
                budget_datasets = budget_filtered_data.get('datasets', [])
                print(f"Budget API Response: labels={len(budget_labels)}, datasets={len(budget_datasets)}")
                
                if len(budget_labels) == 0 and len(budget_datasets) == 0:
                    print("⚠️  EMPTY BUDGET DATA - This could be the issue!")
                else:
                    print("✓ Budget data returned")
            else:
                print(f"Budget API Error: {budget_filtered_response.text}")
            
            # Test expense chart API with account filter
            expense_filtered_url = f"{base_url}/api/expense_breakdown?months=3&include_pending=true&show_subcategories=false&account_ids={account_id}"
            print(f"Expense API URL: {expense_filtered_url}")
            expense_filtered_response = session.get(expense_filtered_url)
            print(f"Expense API Status: {expense_filtered_response.status_code}")
            
            if expense_filtered_response.status_code == 200:
                expense_filtered_data = expense_filtered_response.json()
                expense_labels = expense_filtered_data.get('labels', [])
                expense_datasets = expense_filtered_data.get('datasets', [])
                print(f"Expense API Response: labels={len(expense_labels)}, datasets={len(expense_datasets)}")
                
                if len(expense_labels) == 0 and len(expense_datasets) == 0:
                    print("⚠️  EMPTY EXPENSE DATA - This could be the issue!")
                else:
                    print("✓ Expense data returned")
                    
                # Show some sample data if available
                if expense_datasets and len(expense_datasets) > 0 and 'data' in expense_datasets[0]:
                    sample_data = expense_datasets[0]['data'][:5]  # First 5 data points
                    print(f"Sample expense data: {sample_data}")
            else:
                print(f"Expense API Error: {expense_filtered_response.text}")
        
        # Test with Mercury account filtering
        print(f"\n5. Testing with Mercury account filtering...")
        
        # Find Mercury account dropdown
        mercury_select = reports_soup.find('select', {'name': 'mercury_account_id'})
        mercury_options = mercury_select.find_all('option') if mercury_select else []
        
        mercury_accounts = []
        for option in mercury_options:
            value = option.get('value')
            text = option.get_text(strip=True)
            if value:  # Skip the "All Mercury Accounts" option
                mercury_accounts.append((value, text))
                print(f"Mercury account: {text} (ID: {value})")
        
        if mercury_accounts:
            mercury_id, mercury_name = mercury_accounts[0]
            bank_id, bank_name = accounts[0]
            
            print(f"\nTesting combination: Mercury '{mercury_name}' + Bank '{bank_name}'")
            
            # Test with both Mercury and Bank account filters
            combined_budget_url = f"{base_url}/api/budget_data?months=12&include_pending=true&show_subcategories=false&mercury_account_id={mercury_id}&account_ids={bank_id}"
            print(f"Combined Budget URL: {combined_budget_url}")
            combined_budget_response = session.get(combined_budget_url)
            print(f"Combined Budget Status: {combined_budget_response.status_code}")
            
            if combined_budget_response.status_code == 200:
                combined_budget_data = combined_budget_response.json()
                combined_labels = combined_budget_data.get('labels', [])
                combined_datasets = combined_budget_data.get('datasets', [])
                print(f"Combined Budget Response: labels={len(combined_labels)}, datasets={len(combined_datasets)}")
                
                if len(combined_labels) == 0 and len(combined_datasets) == 0:
                    print("⚠️  EMPTY COMBINED DATA - This is likely the root cause!")
                    print("The issue: Bank account doesn't belong to the selected Mercury account")
                else:
                    print("✓ Combined filtering works")
            else:
                print(f"Combined Budget API Error: {combined_budget_response.text}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Reports page chart API endpoints with account filtering")
    print("=" * 70)
    test_reports_chart_apis()
