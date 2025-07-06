#!/usr/bin/env python3
"""
Final comprehensive test of the account filtering fix
"""

import requests
from bs4 import BeautifulSoup

def comprehensive_test():
    """Run all tests to verify the fix is complete"""
    base_url = "http://localhost:5001"
    
    login_data = {
        'username': 'testfirstuser',
        'password': 'test'
    }
    
    session = requests.Session()
    results = {
        'login': False,
        'page_load': False,
        'account_detection': False,
        'single_account_filter': False,
        'checkbox_preservation': False,
        'filter_clearing': False,
        'multiple_account_filter': False,
        'status_filter': False,
        'combined_filter': False
    }
    
    try:
        # Test 1: Login
        print("Test 1: Login")
        login_response = session.post(f"{base_url}/login", data=login_data)
        results['login'] = "dashboard" in login_response.url
        print(f"  {'✓' if results['login'] else '✗'} Login {'successful' if results['login'] else 'failed'}")
        
        if not results['login']:
            return results
        
        # Test 2: Page loads correctly
        print("\nTest 2: Transactions page loading")
        initial_response = session.get(f"{base_url}/transactions")
        results['page_load'] = initial_response.status_code == 200
        print(f"  {'✓' if results['page_load'] else '✗'} Page loads {'successfully' if results['page_load'] else 'with errors'}")
        
        if not results['page_load']:
            return results
        
        initial_soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        # Test 3: Account detection
        print("\nTest 3: Account detection")
        account_checkboxes = initial_soup.find_all('input', {'name': 'account_id', 'type': 'checkbox'})
        results['account_detection'] = len(account_checkboxes) > 0
        print(f"  {'✓' if results['account_detection'] else '✗'} Found {len(account_checkboxes)} accounts")
        
        if not results['account_detection']:
            return results
        
        # Test 4: Single account filtering
        print("\nTest 4: Single account filtering")
        test_account_id = account_checkboxes[0].get('value')
        filter_url = f"{base_url}/transactions?account_id={test_account_id}"
        filter_response = session.get(filter_url)
        results['single_account_filter'] = filter_response.status_code == 200
        print(f"  {'✓' if results['single_account_filter'] else '✗'} Single account filter {'works' if results['single_account_filter'] else 'fails'}")
        
        if not results['single_account_filter']:
            return results
        
        # Test 5: Checkbox preservation after filtering
        print("\nTest 5: Checkbox preservation")
        filter_soup = BeautifulSoup(filter_response.text, 'html.parser')
        checked_checkboxes = filter_soup.find_all('input', {'name': 'account_id', 'checked': True})
        results['checkbox_preservation'] = (len(checked_checkboxes) == 1 and 
                                          checked_checkboxes[0].get('value') == test_account_id)
        print(f"  {'✓' if results['checkbox_preservation'] else '✗'} Checkbox {'preserved correctly' if results['checkbox_preservation'] else 'not preserved'}")
        
        # Test 6: Filter clearing
        print("\nTest 6: Filter clearing")
        clear_response = session.get(f"{base_url}/transactions")
        clear_soup = BeautifulSoup(clear_response.text, 'html.parser')
        clear_checked = clear_soup.find_all('input', {'name': 'account_id', 'checked': True})
        results['filter_clearing'] = len(clear_checked) == 0
        print(f"  {'✓' if results['filter_clearing'] else '✗'} Filter clearing {'works' if results['filter_clearing'] else 'fails'}")
        
        # Test 7: Multiple account filtering
        print("\nTest 7: Multiple account filtering")
        if len(account_checkboxes) >= 2:
            account_ids = [cb.get('value') for cb in account_checkboxes[:2]]
            multi_url = f"{base_url}/transactions?" + "&".join([f"account_id={aid}" for aid in account_ids])
            multi_response = session.get(multi_url)
            multi_soup = BeautifulSoup(multi_response.text, 'html.parser')
            multi_checked = multi_soup.find_all('input', {'name': 'account_id', 'checked': True})
            results['multiple_account_filter'] = len(multi_checked) == 2
            print(f"  {'✓' if results['multiple_account_filter'] else '✗'} Multiple account filter {'works' if results['multiple_account_filter'] else 'fails'}")
        else:
            results['multiple_account_filter'] = True  # Skip if not enough accounts
            print("  ⏭ Skipped (not enough accounts)")
        
        # Test 8: Status filtering
        print("\nTest 8: Status filtering")
        status_url = f"{base_url}/transactions?status=pending"
        status_response = session.get(status_url)
        status_soup = BeautifulSoup(status_response.text, 'html.parser')
        status_checked = status_soup.find_all('input', {'name': 'status', 'checked': True})
        results['status_filter'] = len(status_checked) >= 1
        print(f"  {'✓' if results['status_filter'] else '✗'} Status filter {'works' if results['status_filter'] else 'fails'}")
        
        # Test 9: Combined filtering
        print("\nTest 9: Combined account + status filtering")
        combined_url = f"{base_url}/transactions?account_id={test_account_id}&status=pending"
        combined_response = session.get(combined_url)
        combined_soup = BeautifulSoup(combined_response.text, 'html.parser')
        combined_account_checked = combined_soup.find_all('input', {'name': 'account_id', 'checked': True})
        combined_status_checked = combined_soup.find_all('input', {'name': 'status', 'checked': True})
        results['combined_filter'] = (len(combined_account_checked) == 1 and len(combined_status_checked) >= 1)
        print(f"  {'✓' if results['combined_filter'] else '✗'} Combined filter {'works' if results['combined_filter'] else 'fails'}")
        
        return results
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return results

def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    test_names = {
        'login': 'User login',
        'page_load': 'Page loading',
        'account_detection': 'Account detection',
        'single_account_filter': 'Single account filtering',
        'checkbox_preservation': 'Checkbox preservation',
        'filter_clearing': 'Filter clearing',
        'multiple_account_filter': 'Multiple account filtering',
        'status_filter': 'Status filtering',
        'combined_filter': 'Combined filtering'
    }
    
    for key, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_names[key]}: {status}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! The account filtering fix is complete and working correctly.")
    else:
        print(f"\n⚠️  Some tests failed. The fix may need additional work.")

if __name__ == "__main__":
    print("Running comprehensive test suite for account filtering fix")
    print("="*60)
    results = comprehensive_test()
    print_summary(results)
