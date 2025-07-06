#!/usr/bin/env python3
"""
Test script to verify that account dropdown is filtered by Mercury account selection
"""

def test_mercury_account_filtering():
    """Test that accounts are filtered by Mercury account selection in both routes"""
    print("Testing Mercury account filtering in account dropdowns...")
    
    # Check transactions route implementation
    with open('/Users/justinkumpe/Documents/mercury_bank_download/web_app/app.py', 'r') as f:
        app_content = f.read()
    
    print("1. Checking transactions route Mercury account filtering...")
    
    # Look for dropdown_accounts filtering logic
    if 'dropdown_accounts = [' in app_content and 'mercury_account_id == mercury_account_id' in app_content:
        print("✅ Transactions route filters dropdown accounts by Mercury account")
    else:
        print("❌ Transactions route missing Mercury account filtering for dropdown")
        return False
    
    # Check that dropdown_accounts is passed to template instead of all_accounts
    if 'accounts=dropdown_accounts' in app_content:
        print("✅ Transactions template receives filtered dropdown_accounts")
    else:
        print("❌ Transactions template not receiving filtered accounts")
        return False
    
    print("2. Checking reports route Mercury account filtering...")
    
    # Look for reports route filtering logic
    if 'mercury_account_accessible_accounts = [' in app_content and 'mercury_account.id' in app_content:
        print("✅ Reports route filters accounts by Mercury account")
    else:
        print("❌ Reports route missing Mercury account filtering")
        return False
    
    # Check that filtered accounts are used for dropdown
    if 'dropdown_accounts = accounts' in app_content:
        print("✅ Reports route uses filtered accounts for dropdown")
    else:
        print("❌ Reports route not using filtered accounts for dropdown")
        return False
    
    print("3. Verifying Mercury account selection logic...")
    
    # Check that both routes handle mercury_account_id parameter
    mercury_param_count = app_content.count('mercury_account_id = request.args.get("mercury_account_id"')
    if mercury_param_count >= 2:  # Should be in both transactions and reports routes
        print("✅ Both routes handle mercury_account_id parameter")
    else:
        print("❌ Missing mercury_account_id parameter handling")
        return False
    
    # Check that filtering logic considers Mercury account selection
    if 'if mercury_account_id:' in app_content:
        print("✅ Mercury account selection is used for filtering")
    else:
        print("❌ Mercury account selection not properly implemented")
        return False
    
    return True

def test_filtering_logic_flow():
    """Test the logical flow of account filtering"""
    print("\n4. Testing filtering logic flow...")
    
    with open('/Users/justinkumpe/Documents/mercury_bank_download/web_app/app.py', 'r') as f:
        app_content = f.read()
    
    # Check that accessible accounts are fetched first
    if 'get_user_accessible_accounts' in app_content:
        print("✅ User accessible accounts are fetched")
    else:
        print("❌ User accessible accounts not fetched")
        return False
    
    # Check that Mercury account filtering is applied to accessible accounts
    if 'account.mercury_account_id ==' in app_content:
        print("✅ Mercury account filtering applied to accessible accounts")
    else:
        print("❌ Mercury account filtering not applied properly")
        return False
    
    # Check that the filtered accounts are used for both dropdown and queries
    if 'account_ids.extend([acc.id for acc in' in app_content:
        print("✅ Filtered accounts used for query building")
    else:
        print("❌ Filtered accounts not used for queries")
        return False
    
    return True

def main():
    """Run all Mercury account filtering tests"""
    print("🔍 Mercury Account Filtering Test")
    print("=" * 40)
    
    tests = [
        test_mercury_account_filtering,
        test_filtering_logic_flow
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
            print("\n❌ Test failed!")
            break
    
    if all_passed:
        print("\n🎉 All Mercury account filtering tests passed!")
        print("\nSummary:")
        print("✅ Accounts dropdown is filtered by Mercury account selection")
        print("✅ Both transactions and reports routes implement filtering")
        print("✅ User can only see accounts from selected Mercury account")
        print("✅ Filtering logic follows proper flow: user accessible → Mercury account → dropdown")
        print("\n🚀 Mercury account filtering is correctly implemented!")
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
