#!/usr/bin/env python3
"""Test script to verify Pushover notifications are working."""

import requests
import os

# Test Pushover notification
app_token = "a8wgjcziktcqja6nrkcteugv9iy58t"
user_key = "u64p9u3himnbrynban5xvjmenhke6g"

if app_token and user_key:
    try:
        data = {
            'token': app_token,
            'user': user_key,
            'message': 'Test notification from Mercury Bank app',
            'title': 'Mercury Bank Test',
            'priority': 1
        }
        
        response = requests.post(
            'https://api.pushover.net/1/messages.json',
            data=data,
            timeout=10
        )
        
        print(f"Pushover API response: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Pushover notification sent successfully!")
        else:
            print("❌ Failed to send Pushover notification")
            
    except Exception as e:
        print(f"❌ Error sending Pushover notification: {e}")
else:
    print("❌ Missing Pushover credentials")
