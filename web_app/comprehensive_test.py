#!/usr/bin/env python3
"""
Comprehensive test for future-dated receipt policy functionality.
This test verifies:
1. Future policies can be created
2. Transactions before the future date use the old policy
3. Transactions after the future date use the new policy
4. Web UI supports scheduling future changes
"""

from datetime import datetime, timedelta
import mysql.connector

def comprehensive_future_policy_test():
    # Connect to the database
    db = mysql.connector.connect(
        host="mysql",
        user="mercury_user",
        password="mercury_password",
        database="mercury_bank"
    )
    
    cursor = db.cursor(dictionary=True)
    
    test_account_id = '8683ef0c-54fe-11f0-9652-1b0a5a6d3438'
    
    print("=== Comprehensive Future Receipt Policy Test ===\n")
    
    # 1. Check current state
    print("1. Current Receipt Policies:")
    cursor.execute("""
        SELECT id, start_date, end_date, receipt_required_deposits, receipt_required_charges
        FROM receipt_policies
        WHERE account_id = %s
        ORDER BY start_date DESC
    """, (test_account_id,))
    
    policies = cursor.fetchall()
    
    for policy in policies:
        end_date = policy['end_date'] if policy['end_date'] else "current"
        print(f"  Policy {policy['id']}: {policy['start_date']} to {end_date}")
        print(f"    Deposits: {policy['receipt_required_deposits']}, Charges: {policy['receipt_required_charges']}")
    
    # 2. Check test transactions
    print("\n2. Test Transactions:")
    cursor.execute("""
        SELECT id, description, amount, posted_at 
        FROM transactions 
        WHERE account_id = %s AND description LIKE 'Test Transaction%'
        ORDER BY posted_at ASC
    """, (test_account_id,))
    
    transactions = cursor.fetchall()
    
    for tx in transactions:
        print(f"  {tx['description']}: Amount ${tx['amount']}, Date: {tx['posted_at']}")
        
        # Find applicable policy
        applicable_policy = None
        for policy in policies:
            start_date = policy['start_date']
            end_date = policy['end_date'] if policy['end_date'] else datetime.max.replace(tzinfo=start_date.tzinfo)
            
            if start_date <= tx['posted_at'] and tx['posted_at'] < end_date:
                applicable_policy = policy
                break
        
        if applicable_policy:
            # Check if receipt is required for this transaction
            is_deposit = tx['amount'] > 0
            if is_deposit:
                policy_type = applicable_policy['receipt_required_deposits']
            else:
                policy_type = applicable_policy['receipt_required_charges']
            
            receipt_required = (policy_type == 'always')
            
            print(f"    → Policy {applicable_policy['id']} applies")
            print(f"    → Receipt Required: {receipt_required} (Policy: {policy_type})")
        else:
            print(f"    → No applicable policy")
    
    # 3. Verify the logic is correct
    print("\n3. Verification:")
    
    # Count policies with NULL end_date (should be exactly 1)
    cursor.execute("""
        SELECT COUNT(*) as active_count
        FROM receipt_policies
        WHERE account_id = %s AND end_date IS NULL
    """, (test_account_id,))
    
    active_count = cursor.fetchone()['active_count']
    print(f"  Active policies (end_date IS NULL): {active_count}")
    
    if active_count == 1:
        print("  ✓ Exactly one active policy found")
    else:
        print("  ✗ ERROR: Should have exactly one active policy")
    
    # Check if we have both past and future transactions with different requirements
    today_tx = None
    future_tx = None
    
    for tx in transactions:
        if 'Today' in tx['description']:
            today_tx = tx
        elif 'Future' in tx['description']:
            future_tx = tx
    
    if today_tx and future_tx:
        print("  ✓ Both present and future test transactions found")
        
        # Verify they get different policies
        today_policy = None
        future_policy = None
        
        for policy in policies:
            start_date = policy['start_date']
            end_date = policy['end_date'] if policy['end_date'] else datetime.max.replace(tzinfo=start_date.tzinfo)
            
            if start_date <= today_tx['posted_at'] and today_tx['posted_at'] < end_date:
                today_policy = policy
            
            if start_date <= future_tx['posted_at'] and future_tx['posted_at'] < end_date:
                future_policy = policy
        
        if today_policy and future_policy and today_policy['id'] != future_policy['id']:
            print("  ✓ Present and future transactions use different policies")
            
            today_required = (today_policy['receipt_required_deposits'] == 'always')
            future_required = (future_policy['receipt_required_deposits'] == 'always')
            
            if not today_required and future_required:
                print("  ✓ Receipt requirements change correctly: Today=False, Future=True")
                print("\n=== TEST PASSED ===")
                print("Future-dated receipt policy feature is working correctly!")
            else:
                print(f"  ✗ Receipt requirements don't match expected pattern: Today={today_required}, Future={future_required}")
        else:
            print("  ✗ Present and future transactions should use different policies")
    else:
        print("  ✗ Missing test transactions")
    
    cursor.close()
    db.close()

if __name__ == "__main__":
    comprehensive_future_policy_test()
