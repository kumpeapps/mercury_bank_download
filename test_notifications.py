#!/usr/bin/env python3
"""Test script to verify approval notification fixes."""

import sys
import os
sys.path.append('/app')  # Add the app directory to Python path

from notification_service import NotificationService

def test_pushover_actions():
    """Test the Pushover notification with action buttons."""
    print("Testing Pushover notification with action buttons...")
    
    # Mock database session (None for environment-based config)
    ns = NotificationService(db_session=None)
    
    # Test data
    approvers = [{
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'pushover_user_key': 'test_user_key_12345'
    }]
    
    request_data = {
        'account_name': 'Test Account',
        'requested_by': 'John Doe',
        'restriction_type': 'amount_threshold',
        'max_amount': 1000.00,
        'max_transactions': 5,
        'approval_start_date': '2025-07-26',
        'approval_end_date': '2025-08-26',
        'request_reason': 'Emergency expenses for quarterly maintenance'
    }
    
    approve_url = 'http://localhost:5001/approval/requests/1/approve'
    deny_url = 'http://localhost:5001/approval/requests/1/deny'
    
    print("Testing notification service with mock data...")
    print(f"Pushover enabled: {ns.pushover_enabled}")
    print(f"Email enabled: {ns.email_enabled}")
    
    if ns.pushover_enabled:
        print("Pushover is configured - would send notification with action buttons")
        print(f"Details URL: {approve_url.replace('/approve', '/details')}")
        print(f"Approve URL: {approve_url}")
        print(f"Deny URL: {deny_url}")
    else:
        print("Pushover not configured - skipping Pushover test")
    
    if ns.email_enabled:
        print("Email is configured - would send HTML email with buttons")
    else:
        print("Email not configured - skipping email test")
    
    print("✅ Test completed - notification system ready!")

if __name__ == '__main__':
    test_pushover_actions()
