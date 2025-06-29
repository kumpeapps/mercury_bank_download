#!/usr/bin/env python3
"""
Mercury Bank Database Setup Script

This script helps initialize the database with the new User and MercuryAccount models.
It also provides examples of how to create initial records for testing.
"""

import os
import sys
import uuid
from datetime import datetime

from models import User, MercuryAccount, Account, Transaction
from models.base import create_engine_and_session, init_db
from sqlalchemy.orm import Session


def setup_database():
    """Initialize the database with all tables."""
    print("Setting up database tables...")
    init_db()
    print("Database tables created successfully!")


def create_sample_mercury_account(db: Session) -> str:
    """
    Create a sample Mercury account group.
    
    Args:
        db: Database session
        
    Returns:
        str: ID of the created Mercury account
    """
    mercury_account_id = str(uuid.uuid4())
    
    sample_mercury_account = MercuryAccount(
        id=mercury_account_id,
        name="Sample Company Mercury Account",
        api_key="your_mercury_api_key_here",  # Replace with actual API key
        sandbox_mode=True,  # Set to False for production
        description="Sample Mercury Bank account group for testing",
        is_active=True,
        sync_enabled=True
    )
    
    db.add(sample_mercury_account)
    print(f"Created sample Mercury account: {mercury_account_id}")
    return mercury_account_id


def create_sample_user(db: Session, mercury_account_id: str) -> str:
    """
    Create a sample user and associate with the Mercury account.
    
    Args:
        db: Database session
        mercury_account_id: ID of the Mercury account to associate with
        
    Returns:
        str: ID of the created user
    """
    user_id = str(uuid.uuid4())
    
    # Get the Mercury account to associate with
    mercury_account = db.query(MercuryAccount).filter(
        MercuryAccount.id == mercury_account_id
    ).first()
    
    if not mercury_account:
        raise ValueError(f"Mercury account {mercury_account_id} not found")
    
    sample_user = User(
        id=user_id,
        username="admin",
        email="admin@company.com",
        password_hash="$2b$12$dummy_hash_replace_with_real_hash",  # Replace with real password hash
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_admin=True
    )
    
    # Associate user with Mercury account
    sample_user.mercury_accounts.append(mercury_account)
    
    db.add(sample_user)
    print(f"Created sample user: {user_id}")
    return user_id


def main():
    """Main setup function."""
    print("Mercury Bank Database Setup")
    print("=" * 40)
    
    # Setup database
    setup_database()
    
    # Ask if user wants to create sample data
    create_samples = input("\nCreate sample data? (y/N): ").lower().strip()
    
    if create_samples == 'y':
        engine, session_local = create_engine_and_session()
        db = session_local()
        
        try:
            # Create sample Mercury account
            mercury_account_id = create_sample_mercury_account(db)
            
            # Create sample user
            user_id = create_sample_user(db, mercury_account_id)
            
            db.commit()
            print("\nSample data created successfully!")
            print(f"Mercury Account ID: {mercury_account_id}")
            print(f"User ID: {user_id}")
            
            print("\nNext steps:")
            print("1. Update the Mercury account with your actual API key")
            print("2. Update the user with a proper password hash")
            print("3. Run the sync script to start syncing data")
            
        except Exception as e:
            db.rollback()
            print(f"Error creating sample data: {e}")
            sys.exit(1)
        finally:
            db.close()
    
    print("\nDatabase setup complete!")


if __name__ == "__main__":
    main()
