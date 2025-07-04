#!/usr/bin/env python3
"""
Temporary script to generate the initial Alembic migration
This will be run outside the containers to bootstrap the migration system
"""
import os
import sys

# Add the sync_app directory to the Python path
sync_app_path = os.path.join(os.path.dirname(__file__), 'sync_app')
sys.path.insert(0, sync_app_path)

# Set up environment variables for database connection
os.environ['DATABASE_URL'] = 'mysql+pymysql://mercury_user:mercury_password@localhost:3306/mercury_bank'

# Import Alembic and SQLAlchemy
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from models.base import Base

def main():
    try:
        # Test database connection
        engine = create_engine(os.environ['DATABASE_URL'])
        with engine.connect() as conn:
            print("✅ Database connection successful")
        
        # Set up Alembic config
        alembic_cfg = Config(os.path.join(sync_app_path, 'alembic.ini'))
        
        # Generate initial migration
        print("🔄 Generating initial migration from models...")
        command.revision(alembic_cfg, autogenerate=True, message="Initial migration from models")
        print("✅ Initial migration generated successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
