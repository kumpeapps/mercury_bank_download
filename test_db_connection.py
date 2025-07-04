#!/usr/bin/env python3
"""
Test database connectivity for Alembic setup
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def test_connection():
    """Test database connection using environment variables."""
    # Load environment variables
    load_dotenv()
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False
    
    print(f"Testing connection to: {database_url.replace(database_url.split('@')[0].split('//')[1], '***:***')}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row[0] == 1:
                print("✅ Database connection successful!")
                
                # Check if we can see tables
                tables_result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in tables_result.fetchall()]
                print(f"📋 Found {len(tables)} tables: {tables}")
                return True
            else:
                print("❌ Database connection test failed")
                return False
                
    except (Exception,) as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
