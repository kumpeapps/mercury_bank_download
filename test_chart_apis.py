#!/usr/bin/env python3
"""
Test script to debug chart API endpoints with authentication
"""

import requests
import json
import sys
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:5001"
LOGIN_URL = urljoin(BASE_URL, "/login")
BUDGET_API_URL = urljoin(BASE_URL, "/api/budget_data")
EXPENSE_API_URL = urljoin(BASE_URL, "/api/expense_breakdown")

def test_chart_apis():
    """Test chart APIs with authentication"""
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("Testing Chart API endpoints...")
    print("=" * 50)
    
    # First, try to login
    print("Step 1: Attempting to login...")
    
    # Get login page to get CSRF token if needed
    login_page = session.get(LOGIN_URL)
    if login_page.status_code != 200:
        print(f"❌ Failed to access login page: {login_page.status_code}")
        return False
    
    # Try to login (you'll need to update these credentials)
    login_data = {
        'username': 'test',  # Update with actual username
        'password': 'test123'  # Update with actual password
    }
    
    login_response = session.post(LOGIN_URL, data=login_data)
    
    if login_response.status_code == 200 and 'login' not in login_response.url:
        print("✅ Login successful")
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response URL: {login_response.url}")
        print("Please update the login credentials in this script")
        return False
    
    # Test budget API without filters
    print("\nStep 2: Testing budget API without filters...")
    budget_response = session.get(BUDGET_API_URL)
    print(f"Status: {budget_response.status_code}")
    
    if budget_response.status_code == 200:
        budget_data = budget_response.json()
        print(f"✅ Budget API success - Labels: {len(budget_data.get('labels', []))}, Datasets: {len(budget_data.get('datasets', []))}")
        if budget_data.get('labels'):
            print(f"Sample labels: {budget_data['labels'][:3]}...")
        if budget_data.get('datasets'):
            print(f"Sample datasets count: {len(budget_data['datasets'])}")
    else:
        print(f"❌ Budget API failed: {budget_response.status_code}")
        print(f"Response: {budget_response.text[:200]}...")
    
    # Test expense API without filters
    print("\nStep 3: Testing expense API without filters...")
    expense_response = session.get(EXPENSE_API_URL)
    print(f"Status: {expense_response.status_code}")
    
    if expense_response.status_code == 200:
        expense_data = expense_response.json()
        print(f"✅ Expense API success - Labels: {len(expense_data.get('labels', []))}, Datasets: {len(expense_data.get('datasets', []))}")
        if expense_data.get('labels'):
            print(f"Sample labels: {expense_data['labels'][:3]}...")
        if expense_data.get('datasets') and expense_data['datasets'][0].get('data'):
            print(f"Sample data points: {len(expense_data['datasets'][0]['data'])}")
    else:
        print(f"❌ Expense API failed: {expense_response.status_code}")
        print(f"Response: {expense_response.text[:200]}...")
    
    # Test with account filter (you'll need to get actual account IDs)
    print("\nStep 4: Testing APIs with account filter...")
    
    # First, let's get available accounts by checking the transactions page
    transactions_url = urljoin(BASE_URL, "/transactions")
    transactions_response = session.get(transactions_url)
    
    if transactions_response.status_code == 200:
        # Parse HTML to find account IDs (simple approach)
        content = transactions_response.text
        if 'Mercury Checking ••3295' in content:
            print("Found Mercury Checking ••3295 account")
            
            # Try to find account ID in the HTML (this is a rough approach)
            import re
            account_pattern = r'value="(\d+)"[^>]*>.*?Mercury Checking.*?3295'
            match = re.search(account_pattern, content, re.DOTALL)
            
            if match:
                account_id = match.group(1)
                print(f"Found account ID: {account_id}")
                
                # Test budget API with account filter
                budget_filtered_url = f"{BUDGET_API_URL}?account_ids={account_id}"
                print(f"Testing: {budget_filtered_url}")
                
                budget_filtered_response = session.get(budget_filtered_url)
                print(f"Budget API with account filter - Status: {budget_filtered_response.status_code}")
                
                if budget_filtered_response.status_code == 200:
                    budget_filtered_data = budget_filtered_response.json()
                    print(f"✅ Budget API filtered success - Labels: {len(budget_filtered_data.get('labels', []))}, Datasets: {len(budget_filtered_data.get('datasets', []))}")
                    
                    # Check if data is empty
                    if not budget_filtered_data.get('labels') or len(budget_filtered_data.get('labels', [])) == 0:
                        print("⚠️  Budget API returned empty data for this account filter")
                    else:
                        print(f"Labels: {budget_filtered_data['labels']}")
                        for i, dataset in enumerate(budget_filtered_data.get('datasets', [])):
                            print(f"Dataset {i}: {dataset.get('label')} - {len(dataset.get('data', []))} data points")
                else:
                    print(f"❌ Budget API filtered failed: {budget_filtered_response.status_code}")
                
                # Test expense API with account filter
                expense_filtered_url = f"{EXPENSE_API_URL}?account_ids={account_id}"
                print(f"Testing: {expense_filtered_url}")
                
                expense_filtered_response = session.get(expense_filtered_url)
                print(f"Expense API with account filter - Status: {expense_filtered_response.status_code}")
                
                if expense_filtered_response.status_code == 200:
                    expense_filtered_data = expense_filtered_response.json()
                    print(f"✅ Expense API filtered success - Labels: {len(expense_filtered_data.get('labels', []))}, Datasets: {len(expense_filtered_data.get('datasets', []))}")
                    
                    # Check if data is empty
                    if not expense_filtered_data.get('labels') or len(expense_filtered_data.get('labels', [])) == 0:
                        print("⚠️  Expense API returned empty data for this account filter")
                    else:
                        print(f"Labels: {expense_filtered_data['labels']}")
                        if expense_filtered_data.get('datasets') and expense_filtered_data['datasets'][0].get('data'):
                            print(f"Data points: {expense_filtered_data['datasets'][0]['data']}")
                else:
                    print(f"❌ Expense API filtered failed: {expense_filtered_response.status_code}")
            else:
                print("Could not extract account ID from transactions page")
        else:
            print("Could not find Mercury Checking ••3295 account on transactions page")
    else:
        print(f"❌ Failed to access transactions page: {transactions_response.status_code}")
    
    print("\n" + "=" * 50)
    print("Chart API testing complete!")
    return True

if __name__ == "__main__":
    test_chart_apis()
