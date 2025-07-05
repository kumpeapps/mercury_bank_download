#!/usr/bin/env python3
from datetime import datetime
import mysql.connector

def check_receipt_policy_for_transactions():
    # Connect to the database
    db = mysql.connector.connect(
        host="mysql",
        user="mercury_user",
        password="mercury_password",
        database="mercury_bank"
    )
    
    cursor = db.cursor(dictionary=True)
    
    # Get transactions for the account
    cursor.execute("""
        SELECT id, description, amount, posted_at 
        FROM transactions 
        WHERE account_id = '8683ef0c-54fe-11f0-9652-1b0a5a6d3438' 
        ORDER BY posted_at DESC
    """)
    
    transactions = cursor.fetchall()
    
    # Get receipt policies for the account
    cursor.execute("""
        SELECT id, start_date, end_date, receipt_required_deposits, receipt_required_charges
        FROM receipt_policies
        WHERE account_id = '8683ef0c-54fe-11f0-9652-1b0a5a6d3438'
        ORDER BY start_date DESC
    """)
    
    policies = cursor.fetchall()
    
    print("Receipt Policies:")
    for policy in policies:
        end_date = policy['end_date'] if policy['end_date'] else "current"
        print(f"Policy {policy['id']}: {policy['start_date']} to {end_date}")
        print(f"  Deposits: {policy['receipt_required_deposits']}, Charges: {policy['receipt_required_charges']}")
    
    print("\nTransactions:")
    for tx in transactions:
        print(f"Transaction {tx['id']}: {tx['description']}, Amount: {tx['amount']}, Date: {tx['posted_at']}")
        
        # Find applicable policy
        applicable_policy = None
        for policy in policies:
            start_date = policy['start_date']
            end_date = policy['end_date'] if policy['end_date'] else datetime.max
            
            if start_date <= tx['posted_at'] and tx['posted_at'] < end_date:
                applicable_policy = policy
                break
        
        if applicable_policy:
            receipt_required = False
            if tx['amount'] > 0:  # Deposit
                policy_type = applicable_policy['receipt_required_deposits']
                if policy_type == 'always':
                    receipt_required = True
            else:  # Charge
                policy_type = applicable_policy['receipt_required_charges']
                if policy_type == 'always':
                    receipt_required = True
            
            print(f"  Applies Policy {applicable_policy['id']}: {applicable_policy['start_date']} to {applicable_policy['end_date'] if applicable_policy['end_date'] else 'current'}")
            print(f"  Receipt Required: {receipt_required}")
        else:
            print("  No applicable policy found")
    
    cursor.close()
    db.close()

if __name__ == "__main__":
    check_receipt_policy_for_transactions()
