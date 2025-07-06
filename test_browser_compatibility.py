#!/usr/bin/env python3
"""
Test browser compatibility and cache-busting for transaction filtering
"""

import requests
import time

def test_browser_compatibility():
    """Test with different user agents and cache-busting"""
    base_url = "http://localhost:5001"
    
    login_data = {
        'username': 'testfirstuser',
        'password': 'testpass123'
    }
    
    # Test with different user agents
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',  # Chrome-like
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',  # Safari-like
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101'  # Firefox-like
    ]
    
    for i, user_agent in enumerate(user_agents, 1):
        print(f"\n{i}. Testing with user agent: {user_agent[:50]}...")
        
        session = requests.Session()
        session.headers.update({'User-Agent': user_agent})
        
        try:
            # Login
            login_response = session.post(f"{base_url}/login", data=login_data)
            if "dashboard" not in login_response.url:
                print(f"   ✗ Login failed")
                continue
            
            # Test filtering with cache busting
            account_id = '867a1270-54fe-11f0-9652-b7f2a577d83a'
            cache_buster = int(time.time())
            test_url = f"{base_url}/transactions?account_id={account_id}&_={cache_buster}"
            
            response = session.get(test_url)
            if response.status_code != 200:
                print(f"   ✗ Request failed: {response.status_code}")
                continue
            
            # Check if checkbox is preserved
            if f'value="{account_id}"' in response.text and 'checked' in response.text:
                print(f"   ✓ Filtering works with this user agent")
            else:
                print(f"   ✗ Filtering doesn't work with this user agent")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")

def test_manual_simulation():
    """Simulate manual user interaction"""
    base_url = "http://localhost:5001"
    
    login_data = {
        'username': 'testfirstuser',
        'password': 'testpass123'
    }
    
    session = requests.Session()
    
    try:
        print("\nSimulating manual user interaction:")
        
        # Step 1: Login
        print("1. User logs in...")
        login_response = session.post(f"{base_url}/login", data=login_data)
        if "dashboard" not in login_response.url:
            print("   ✗ Login failed")
            return False
        print("   ✓ Login successful")
        
        # Step 2: Navigate to transactions
        print("2. User navigates to transactions page...")
        transactions_response = session.get(f"{base_url}/transactions")
        if transactions_response.status_code != 200:
            print("   ✗ Failed to load transactions page")
            return False
        print("   ✓ Transactions page loaded")
        
        # Step 3: User sees available accounts
        import re
        accounts = re.findall(r'name="account_id" value="([^"]+)"', transactions_response.text)
        print(f"   ✓ User sees {len(accounts)} available accounts")
        
        # Step 4: User selects first account and clicks Filter
        print("3. User selects first account and clicks Filter button...")
        selected_account = accounts[0]
        
        # This simulates clicking the Filter button with the first account selected
        filter_url = f"{base_url}/transactions?account_id={selected_account}"
        filter_response = session.get(filter_url)
        
        if filter_response.status_code != 200:
            print("   ✗ Filter request failed")
            return False
        
        # Step 5: Check if the page shows the account as selected
        filter_content = filter_response.text
        checkbox_pattern = rf'value="{re.escape(selected_account)}"[^>]*checked'
        
        if re.search(checkbox_pattern, filter_content):
            print(f"   ✓ Account {selected_account[:8]}... checkbox remains checked after filtering")
            print("   ✓ FILTERING IS WORKING CORRECTLY")
            return True
        else:
            print(f"   ✗ Account {selected_account[:8]}... checkbox is NOT checked after filtering")
            print("   ✗ FILTERING IS NOT WORKING")
            
            # Debug: Show the actual checkbox HTML
            checkbox_search = re.search(rf'<input[^>]*value="{re.escape(selected_account)}"[^>]*>', filter_content)
            if checkbox_search:
                print(f"   Debug - Actual checkbox HTML: {checkbox_search.group(0)}")
            else:
                print("   Debug - Checkbox not found in HTML")
            
            return False
            
    except Exception as e:
        print(f"Error during manual simulation: {e}")
        return False

if __name__ == "__main__":
    print("Testing browser compatibility and manual interaction")
    print("=" * 60)
    
    # Test browser compatibility
    test_browser_compatibility()
    
    # Test manual simulation
    manual_works = test_manual_simulation()
    
    print("\n" + "=" * 60)
    if manual_works:
        print("✅ CONCLUSION: Transaction filtering is working correctly!")
        print("")
        print("If you're still experiencing issues, please try:")
        print("1. Clear your browser cache (Cmd+Shift+R or Ctrl+Shift+R)")
        print("2. Try in incognito/private browsing mode")
        print("3. Try a different browser")
        print("4. Make sure you're logged in as the test user")
        print("5. Check browser console for JavaScript errors")
    else:
        print("❌ CONCLUSION: There may still be issues with transaction filtering")
    
    exit(0 if manual_works else 1)
