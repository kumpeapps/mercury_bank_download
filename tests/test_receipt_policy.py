import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sync_app.models import Account, ReceiptPolicy, Base
from decimal import Decimal
import sys

class TestReceiptPolicy(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine('sqlite:///:memory:')
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
        self.session = self.Session()
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create test account
        account = Account(
            id="test_account_123",
            name="Test Account",
            currency="USD",
            status="open",
            receipt_required_deposits="threshold",
            receipt_threshold_deposits=100.0,
            receipt_required_charges="threshold",
            receipt_threshold_charges=50.0
        )
        self.session.add(account)
        self.session.commit()
        
        # Store the account for later use
        self.account = account
        
    def tearDown(self):
        self.Session.remove()
        Base.metadata.drop_all(self.engine)
        
    def test_receipt_policy_creation(self):
        """Test that creating a receipt policy works through the Account.update_receipt_policy method"""
        # Change the receipt settings to trigger policy creation
        self.account.update_receipt_policy(
            receipt_required_deposits="always",
            receipt_threshold_deposits=None,
            receipt_required_charges="threshold",
            receipt_threshold_charges=75.0
        )
        self.session.commit()
        
        # Check that a policy was created
        policies = self.session.query(ReceiptPolicy).filter_by(account_id=self.account.id).all()
        
        # There should be one policy
        self.assertEqual(len(policies), 1)
        
        # Check policy values match what we set
        policy = policies[0]
        self.assertEqual(policy.receipt_required_deposits, "always")
        self.assertIsNone(policy.receipt_threshold_deposits)
        self.assertEqual(policy.receipt_required_charges, "threshold")
        self.assertEqual(policy.receipt_threshold_charges, 75.0)
        self.assertIsNone(policy.end_date)
        
        # Also check the account itself was updated
        self.assertEqual(self.account.receipt_required_deposits, "always")
        self.assertIsNone(self.account.receipt_threshold_deposits)
        self.assertEqual(self.account.receipt_required_charges, "threshold")
        self.assertEqual(self.account.receipt_threshold_charges, 75.0)
        
    def test_receipt_policy_update(self):
        """Test that updating receipt policy works and creates history"""
        # First create an account with different settings than our first policy
        account = Account(
            id="test_account_update",
            name="Test Account Update",
            currency="USD",
            status="open",
            receipt_required_deposits="none",  # Different from first policy
            receipt_threshold_deposits=None,   # Different from first policy 
            receipt_required_charges="none",   # Different from first policy
            receipt_threshold_charges=None     # Different from first policy
        )
        self.session.add(account)
        self.session.commit()
        
        print("\nCreating initial policy...")
        account.update_receipt_policy(
            receipt_required_deposits="threshold",
            receipt_threshold_deposits=100.0,
            receipt_required_charges="threshold",
            receipt_threshold_charges=50.0
        )
        self.session.commit()
        
        # Verify initial policy was created
        initial_policies = self.session.query(ReceiptPolicy).filter_by(account_id=account.id).all()
        print(f"After initial policy creation, found {len(initial_policies)} policies")
        for p in initial_policies:
            print(f"  Policy: {p}, end_date={p.end_date}")
        
        # Update policy with new values
        print("\nUpdating policy...")
        account.update_receipt_policy(
            receipt_required_deposits="always",
            receipt_threshold_deposits=None,
            receipt_required_charges="none",
            receipt_threshold_charges=None
        )
        self.session.commit()
        
        # Check that we now have two policies
        policies = self.session.query(ReceiptPolicy)\
            .filter_by(account_id=account.id)\
            .order_by(ReceiptPolicy.start_date)\
            .all()
        
        print(f"After update, found {len(policies)} policies")
        for p in policies:
            print(f"  Policy: {p}, end_date={p.end_date}")
        
        self.assertEqual(len(policies), 2)
        
        # First policy should be ended and have original values
        self.assertEqual(policies[0].receipt_required_deposits, "threshold")
        self.assertEqual(policies[0].receipt_threshold_deposits, 100.0)
        self.assertEqual(policies[0].receipt_required_charges, "threshold")
        self.assertEqual(policies[0].receipt_threshold_charges, 50.0)
        self.assertIsNotNone(policies[0].end_date)
        
        # Second policy should have updated values and no end date
        self.assertEqual(policies[1].receipt_required_deposits, "always")
        self.assertIsNone(policies[1].receipt_threshold_deposits)
        self.assertEqual(policies[1].receipt_required_charges, "none")
        self.assertIsNone(policies[1].receipt_threshold_charges)
        self.assertIsNone(policies[1].end_date)
        
        # First policy should be ended and have original values
        self.assertEqual(policies[0].receipt_required_deposits, "threshold")
        self.assertEqual(policies[0].receipt_threshold_deposits, 100.0)
        self.assertEqual(policies[0].receipt_required_charges, "threshold")
        self.assertEqual(policies[0].receipt_threshold_charges, 50.0)
        self.assertIsNotNone(policies[0].end_date)
        
        # Second policy should have updated values and no end date
        self.assertEqual(policies[1].receipt_required_deposits, "always")
        self.assertIsNone(policies[1].receipt_threshold_deposits)
        self.assertEqual(policies[1].receipt_required_charges, "none")
        self.assertIsNone(policies[1].receipt_threshold_charges)
        self.assertIsNone(policies[1].end_date)
        
    def test_manual_receipt_policy_creation(self):
        """Test direct creation of a ReceiptPolicy without using Account.update_receipt_policy"""
        # Create policy directly
        policy = ReceiptPolicy(
            account_id=self.account.id,
            start_date=datetime.now(),
            receipt_required_deposits="threshold",
            receipt_threshold_deposits=100.0,
            receipt_required_charges="threshold",
            receipt_threshold_charges=50.0
        )
        self.session.add(policy)
        self.session.commit()
        
        # Check that the policy was created
        policies = self.session.query(ReceiptPolicy).filter_by(account_id=self.account.id).all()
        
        self.assertEqual(len(policies), 1)
        
        # Policy should have the correct values
        self.assertEqual(policies[0].receipt_required_deposits, "threshold")
        self.assertEqual(policies[0].receipt_threshold_deposits, 100.0)
        self.assertEqual(policies[0].receipt_required_charges, "threshold")
        self.assertEqual(policies[0].receipt_threshold_charges, 50.0)
        self.assertIsNone(policies[0].end_date)
        
    def test_receipt_requirement_for_transaction_date(self):
        """Test that the system applies the correct receipt policy based on transaction date"""
        # Create an initial policy from a month ago
        one_month_ago = datetime.now() - timedelta(days=30)
        yesterday = datetime.now() - timedelta(days=1)
        
        # Create two policies with different settings
        policy1 = ReceiptPolicy(
            account_id=self.account.id,
            start_date=one_month_ago,
            end_date=yesterday,
            receipt_required_deposits="threshold",
            receipt_threshold_deposits=100.0,
            receipt_required_charges="threshold",
            receipt_threshold_charges=50.0
        )
        
        policy2 = ReceiptPolicy(
            account_id=self.account.id,
            start_date=datetime.now(),
            end_date=None,
            receipt_required_deposits="always",
            receipt_threshold_deposits=None,
            receipt_required_charges="none",
            receipt_threshold_charges=None
        )
        
        self.session.add_all([policy1, policy2])
        self.session.commit()
        
        # Test a charge transaction from 15 days ago (should use policy1)
        transaction_date = datetime.now() - timedelta(days=15)
        
        # Small charge (-$30) - under threshold, should not require receipt
        self.assertFalse(self.account.is_receipt_required_for_amount(-30.0, transaction_date))
        
        # Large charge (-$75) - over threshold, should require receipt
        self.assertTrue(self.account.is_receipt_required_for_amount(-75.0, transaction_date))
        
        # Test a current transaction (should use policy2)
        transaction_date = datetime.now()
        
        # Any deposit should require receipt with "always" setting
        self.assertTrue(self.account.is_receipt_required_for_amount(10.0, transaction_date))
        
        # Charges should never require receipt with "none" setting
        self.assertFalse(self.account.is_receipt_required_for_amount(-100.0, transaction_date))
        
    def test_get_receipt_status_for_transaction(self):
        """Test the method that determines receipt status for UI display"""
        # Create policies for different time periods
        past_date = datetime.now() - timedelta(days=15)
        policy = ReceiptPolicy(
            account_id=self.account.id,
            start_date=past_date - timedelta(days=15),
            end_date=past_date + timedelta(days=1),
            receipt_required_deposits="always",
            receipt_threshold_deposits=None,
            receipt_required_charges="always", 
            receipt_threshold_charges=None
        )
        self.session.add(policy)
        self.session.commit()
        
        # Test receipt status for a transaction in that time period
        transaction_date = past_date
        
        # Required + Present = required_present (green)
        self.assertEqual(
            self.account.get_receipt_status_for_transaction(100.0, True, transaction_date),
            "required_present"
        )
        
        # Required + Missing = required_missing (red)
        self.assertEqual(
            self.account.get_receipt_status_for_transaction(100.0, False, transaction_date),
            "required_missing"
        )
        
        # For current transactions (using account settings, not policy)
        # Optional + Present = optional_present (blue)
        self.account.receipt_required_deposits = "none"
        self.account.receipt_required_charges = "none"
        self.session.commit()
        
        self.assertEqual(
            self.account.get_receipt_status_for_transaction(100.0, True),
            "optional_present"
        )
        
        # Optional + Missing = optional_missing (blank)
        self.assertEqual(
            self.account.get_receipt_status_for_transaction(100.0, False),
            "optional_missing"
        )
        
    def test_update_receipt_policy_no_changes(self):
        """Test that update_receipt_policy does nothing when settings haven't changed"""
        # First create an initial policy
        self.account.update_receipt_policy(
            receipt_required_deposits="always",
            receipt_threshold_deposits=None,
            receipt_required_charges="none",
            receipt_threshold_charges=None
        )
        self.session.commit()
        
        # Now call update with the same values
        self.account.update_receipt_policy(
            receipt_required_deposits="always",
            receipt_threshold_deposits=None,
            receipt_required_charges="none",
            receipt_threshold_charges=None
        )
        self.session.commit()
        
        # We should still have only one policy
        policies = self.session.query(ReceiptPolicy).filter_by(account_id=self.account.id).all()
        self.assertEqual(len(policies), 1)
        
if __name__ == '__main__':
    unittest.main()
