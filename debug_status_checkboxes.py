#!/usr/bin/env python3
"""
Debug script to examine status checkbox states
"""

import requests
from urllib.parse import urlencode

def debug_status_checkboxes():
    """Debug status checkbox states in HTML output"""
    base_url = "http://localhost:5001"
    
    login_data = {
        'username': 'testfirstuser',
        'password': 'testpass123'
    }
    
    session = requests.Session()
    
    try:
        # Login
        login_response = session.post(f"{base_url}/login", data=login_data)
        if login_response.status_code != 200:
            print("Login failed")
            return
        
        # Test with status filter
        params = {
            'status': ['posted', 'pending']
        }
        query_string = urlencode(params, doseq=True)
        test_url = f"{base_url}/transactions?{query_string}"
        
        print(f"Testing URL: {test_url}")
        
        response = session.get(test_url)
        content = response.text
        
        # Find all status-related inputs
        print("All status inputs:")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'name="status"' in line:
                print(f"Line {i}: {line.strip()}")
                
        # Look for posted status specifically
        search_text = 'value="posted"'
        search_start = content.find(search_text)
        if search_start == -1:
            print(f"Status 'posted' not found in HTML")
        else:
            # Get context around the checkbox
            context_start = max(0, search_start - 100)
            context_end = min(len(content), search_start + 100)
            context = content[context_start:context_end]
            
            print(f"\nHTML context around status 'posted':")
            print("-" * 80)
            print(context)
            print("-" * 80)
            
        # Look for pending status specifically
        search_text = 'value="pending"'
        search_start = content.find(search_text)
        if search_start == -1:
            print(f"Status 'pending' not found in HTML")
        else:
            # Get context around the checkbox
            context_start = max(0, search_start - 100)
            context_end = min(len(content), search_start + 100)
            context = content[context_start:context_end]
            
            print(f"\nHTML context around status 'pending':")
            print("-" * 80)
            print(context)
            print("-" * 80)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_status_checkboxes()
