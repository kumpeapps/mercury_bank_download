#!/usr/bin/env python3
"""
Test script to verify first user registration and admin role assignment
"""

import os
import sys
import requests
import time

def test_registration():
    """Test user registration via HTTP POST"""
    url = "http://localhost:5001/register"
    
    data = {
        'username': 'testfirstuser',
        'email': 'testfirstuser@example.com',
        'password': 'testpass123'
    }
    
    print("Testing user registration...")
    print(f"Registration URL: {url}")
    print(f"User data: {data}")
    
    try:
        # First, get the registration page to establish session
        response = requests.get(url)
        print(f"GET registration page status: {response.status_code}")
        
        # Now submit the registration
        response = requests.post(url, data=data, allow_redirects=False)
        print(f"POST registration status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Registration successful (redirected to login)")
            return True
        elif response.status_code == 200:
            print("⚠️  Registration returned 200 - check for errors on page")
            print("Response content snippet:", response.text[:500])
            return False
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return False

if __name__ == "__main__":
    success = test_registration()
    sys.exit(0 if success else 1)
