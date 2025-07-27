#!/usr/bin/env python3
"""
Migration script to add merchant_filter column to transaction approval tables.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment variables."""
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_user = os.getenv('DB_USER', 'mercury_user')
    db_password = os.getenv('DB_PASSWORD', 'mercury_password')
    db_name = os.getenv('DB_NAME', 'mercury_bank')
    
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def run_migration():
    """Add merchant_filter column to approval tables."""
    engine = create_engine(get_database_url())
    
    with engine.connect() as conn:
        try:
            print("Adding merchant_filter column to transaction_approval_requests...")
            conn.execute(text("""
                ALTER TABLE transaction_approval_requests 
                ADD COLUMN merchant_filter VARCHAR(255) NULL 
                COMMENT 'Merchant name filter (based on counterparty_name)'
            """))
            
            print("Adding merchant_filter column to transaction_approvals...")
            conn.execute(text("""
                ALTER TABLE transaction_approvals 
                ADD COLUMN merchant_filter VARCHAR(255) NULL 
                COMMENT 'Merchant name filter (based on counterparty_name)'
            """))
            
            conn.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    run_migration()
