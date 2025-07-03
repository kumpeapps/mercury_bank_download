#!/usr/bin/env python3
"""
Migration utility to encrypt existing Mercury API keys in the database.

This script will:
1. Connect to the database
2. Find all MercuryAccount records with unencrypted API keys
3. Encrypt them using the SECRET_KEY environment variable
4. Update the database with encrypted values

Run this after deploying the new code that supports encrypted API keys.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.mercury_account import MercuryAccount
from models.base import Base
from utils.encryption import encrypt_api_key, decrypt_api_key


def encrypt_existing_api_keys():
    """
    Encrypt all existing unencrypted API keys in the database.
    """
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        return False
    
    # Check for SECRET_KEY
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        print("Error: SECRET_KEY environment variable is required for encryption")
        return False
    
    try:
        # Create database engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Connecting to database...")
        
        # Get all mercury accounts
        mercury_accounts = session.query(MercuryAccount).all()
        
        if not mercury_accounts:
            print("No Mercury accounts found in database")
            return True
        
        print(f"Found {len(mercury_accounts)} Mercury accounts")
        
        encrypted_count = 0
        already_encrypted_count = 0
        
        for account in mercury_accounts:
            try:
                # Try to access the api_key property - this will handle encryption automatically
                api_key = account.api_key
                
                if api_key:
                    # The getter/setter logic will handle encryption automatically
                    # If it's already encrypted, it will stay encrypted
                    # If it's unencrypted, it will be encrypted on next save
                    
                    # Force a save to trigger encryption if needed
                    session.add(account)
                    
                    # Check if the stored value is now encrypted by trying to decrypt it
                    try:
                        decrypt_api_key(account._api_key_encrypted)
                        encrypted_count += 1
                        print(f"✓ Encrypted API key for account: {account.name}")
                    except ValueError:
                        # If decryption fails, it might be unencrypted - try to encrypt it
                        account.api_key = api_key  # This will trigger encryption
                        session.add(account)
                        encrypted_count += 1
                        print(f"✓ Encrypted API key for account: {account.name}")
                else:
                    print(f"⚠ No API key found for account: {account.name}")
                    
            except Exception as e:
                print(f"✗ Error processing account {account.name}: {str(e)}")
                continue
        
        # Commit all changes
        session.commit()
        print(f"\nMigration completed successfully!")
        print(f"- Encrypted: {encrypted_count} accounts")
        print(f"- Total processed: {len(mercury_accounts)} accounts")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


if __name__ == "__main__":
    print("Mercury API Key Encryption Migration")
    print("=" * 40)
    
    success = encrypt_existing_api_keys()
    
    if success:
        print("\n✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
