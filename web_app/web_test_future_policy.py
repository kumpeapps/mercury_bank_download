#!/usr/bin/env python3
from datetime import datetime, timedelta
import sys
from sqlalchemy.orm import Session

# Import Flask app to get the Session
from app import Session, app
from models.account import Account
from models.receipt_policy import ReceiptPolicy

def test_future_receipt_policy():
    session = Session()
    try:
        # Get an account to test with
        account = session.query(Account).first()
        if not account:
            print("No accounts found in the database.")
            return
        
        print(f"Testing with account: {account.id} ({account.name})")
        
        # Get current receipt policy
        current_policy = (
            session.query(ReceiptPolicy)
            .filter(
                ReceiptPolicy.account_id == account.id,
                ReceiptPolicy.end_date.is_(None)
            )
            .order_by(ReceiptPolicy.start_date.desc())
            .first()
        )
        
        if current_policy:
            print(f"Current policy: starts {current_policy.start_date}, deposits: {current_policy.receipt_required_deposits}, charges: {current_policy.receipt_required_charges}")
        else:
            print("No current policy found.")
        
        # Create a future date (7 days from now)
        future_date = datetime.now() + timedelta(days=7)
        print(f"Setting future policy to start at: {future_date}")
        
        # Create new policy with future date
        account.update_receipt_policy(
            receipt_required_deposits="always",
            receipt_threshold_deposits=None,
            receipt_required_charges="always",
            receipt_threshold_charges=None,
            start_date=future_date
        )
        
        session.commit()
        
        # Verify policies for this account
        policies = (
            session.query(ReceiptPolicy)
            .filter(ReceiptPolicy.account_id == account.id)
            .order_by(ReceiptPolicy.start_date.desc())
            .all()
        )
        
        print(f"Found {len(policies)} policies for account:")
        for policy in policies:
            print(f"  ID: {policy.id}, Start: {policy.start_date}, End: {policy.end_date}")
            print(f"    Deposits: {policy.receipt_required_deposits}, Charges: {policy.receipt_required_charges}")
        
        # Check if we have exactly one active policy (end_date is None)
        active_policies = [p for p in policies if p.end_date is None]
        print(f"Active policies: {len(active_policies)}")
        
        if len(active_policies) == 1 and active_policies[0].start_date > datetime.now():
            print("SUCCESS: Future policy is correctly scheduled!")
        else:
            print("ERROR: Future policy not properly scheduled.")
    finally:
        session.close()

if __name__ == "__main__":
    with app.app_context():
        test_future_receipt_policy()
