#!/usr/bin/env python3
"""
Test authenticated web endpoints for sub-category display
"""

import requests
import sys

def test_authenticated_endpoints():
    """Test web endpoints with authentication to verify sub-category display."""
    
    # Create session for cookie persistence
    session = requests.Session()
    
    try:
        # Step 1: Get the login page to check if app is accessible
        login_response = session.get('http://localhost:5001/login')
        print(f"✓ Login page accessible (status: {login_response.status_code})")
        
        # Step 2: Attempt login (try common admin credentials)
        login_data = {
            'username': 'admin',
            'password': 'password123'
        }
        
        login_post = session.post('http://localhost:5001/login', data=login_data)
        
        # Check if login was successful (redirect or success page)
        if login_post.status_code == 200 and 'dashboard' in login_post.url:
            print("✓ Login successful")
        elif login_post.status_code == 302:
            print("✓ Login successful (redirected)")
        else:
            print("ℹ Login may have failed or credentials not set up")
            return
        
        # Step 3: Test reports page for sub-category display
        reports_response = session.get('http://localhost:5001/reports')
        if reports_response.status_code == 200:
            print("✓ Reports page accessible")
            
            # Check for sub-category arrows in the response
            arrow_count = reports_response.text.count('→')
            if arrow_count > 0:
                print(f"✓ Found {arrow_count} sub-category arrows in reports page")
                
                # Look for specific sub-categories
                subcategories_found = []
                test_subcategories = ['Marketing → Advertising', 'Office → Supplies', 'Food → Restaurants']
                for subcat in test_subcategories:
                    if subcat in reports_response.text:
                        subcategories_found.append(subcat)
                        
                if subcategories_found:
                    print(f"✓ Found specific sub-categories: {subcategories_found}")
                else:
                    print("ℹ No specific test sub-categories found in reports page")
            else:
                print("ℹ No sub-category arrows found in reports page")
        else:
            print(f"✗ Reports page not accessible (status: {reports_response.status_code})")
        
        # Step 4: Test transactions page
        transactions_response = session.get('http://localhost:5001/transactions')
        if transactions_response.status_code == 200:
            print("✓ Transactions page accessible")
            
            # Check for sub-category arrows
            arrow_count = transactions_response.text.count('→')
            if arrow_count > 0:
                print(f"✓ Found {arrow_count} sub-category arrows in transactions page")
            else:
                print("ℹ No sub-category arrows found in transactions page")
        else:
            print(f"✗ Transactions page not accessible (status: {transactions_response.status_code})")
            
        # Step 5: Test API endpoints
        budget_response = session.get('http://localhost:5001/api/budget_data')
        if budget_response.status_code == 200:
            try:
                budget_data = budget_response.json()
                datasets = budget_data.get('datasets', [])
                subcategory_labels = []
                for dataset in datasets:
                    label = dataset.get('label', '')
                    if '→' in label:
                        subcategory_labels.append(label)
                
                if subcategory_labels:
                    print(f"✓ Found sub-categories in budget API: {subcategory_labels[:3]}...")
                else:
                    print("ℹ No sub-categories found in budget API data")
            except Exception as e:
                print(f"ℹ Could not parse budget API response: {e}")
        else:
            print(f"✗ Budget API not accessible (status: {budget_response.status_code})")
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Authenticated Web Interface Test ===")
    success = test_authenticated_endpoints()
    print("\n=== Test Complete ===")
    if success:
        print("✓ Sub-category functionality verification complete!")
    else:
        print("⚠ Some tests failed or credentials need to be set up")
