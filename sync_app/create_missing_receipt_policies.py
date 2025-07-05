#!/usr/bin/env python3
"""
Utility script to ensure all existing accounts have receipt policies.

This script should be run after applying the migrations that created the receipt_policies table.
It will check all accounts and create a receipt policy record for any account that doesn't have one.
"""
import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker, scoped_session

# Set up proper imports that work both in container and local development
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    # Try importing directly (container environment)
    from models.account import Account
    from models.receipt_policy import ReceiptPolicy
    from models.base import create_engine_and_session
except ImportError:
    # Try importing via package (local development environment)
    from sync_app.models.account import Account
    from sync_app.models.receipt_policy import ReceiptPolicy
    from sync_app.models.base import create_engine_and_session

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_missing_receipt_policies():
    """Check all accounts and create receipt policies for those without one."""
    # Create database engine and session using the application's connection function
    try:
        engine, session_factory = create_engine_and_session()
        session = session_factory()
        logger.info("Successfully connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise
    
    try:
        # Get all active accounts
        accounts = session.query(Account).filter(Account.is_active == True).all()
        logger.info(f"Found {len(accounts)} active accounts")
        
        created_count = 0
        for account in accounts:
            # Check if account already has a receipt policy
            existing_policy = (
                session.query(ReceiptPolicy)
                .filter(
                    ReceiptPolicy.account_id == account.id,
                    or_(
                        ReceiptPolicy.end_date.is_(None),
                        ReceiptPolicy.end_date >= datetime.now()
                    )
                )
                .first()
            )
            
            if existing_policy is None:
                # Create a new receipt policy for this account
                logger.info(f"Creating receipt policy for account {account.id} ({account.name})")
                
                # Create policy with current account settings
                policy = ReceiptPolicy(
                    account_id=account.id,
                    start_date=datetime.now(),
                    end_date=None,  # Still active
                    receipt_required_deposits=account.receipt_required_deposits or "none",
                    receipt_threshold_deposits=account.receipt_threshold_deposits,
                    receipt_required_charges=account.receipt_required_charges or "none",
                    receipt_threshold_charges=account.receipt_threshold_charges
                )
                
                session.add(policy)
                created_count += 1
            
        # Commit all changes
        session.commit()
        logger.info(f"Created {created_count} receipt policies")
        
    except Exception as e:
        logger.error(f"Error creating receipt policies: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    logger.info("Starting receipt policy population script")
    create_missing_receipt_policies()
    logger.info("Receipt policy population complete")
