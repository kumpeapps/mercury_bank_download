#!/usr/bin/env python3
"""
Update database schema to include system settings and user access features.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.system_setting import SystemSetting

def update_database_schema():
    """Update the database schema to include new features."""
    
    # Database configuration
    DATABASE_URL = os.environ.get(
        "DATABASE_URL", "mysql+pymysql://user:password@localhost:3306/mercury_bank"
    )
    
    print(f"Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    try:
        # Create all tables
        print("Creating/updating database tables...")
        Base.metadata.create_all(engine)
        print("✓ Database tables created/updated successfully")
        
        # Initialize system settings
        db_session = Session()
        try:
            print("Initializing system settings...")
            
            # Check if users table is a view to set default signup behavior
            try:
                result = db_session.execute(text("""
                    SELECT TABLE_TYPE 
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'users'
                """)).fetchone()
                
                default_signup_enabled = result[0] != 'VIEW' if result else True
                print(f"  - Users table type: {result[0] if result else 'TABLE'}")
                print(f"  - Default signup enabled: {default_signup_enabled}")
            except Exception as e:
                print(f"  - Warning: Could not check users table type: {e}")
                default_signup_enabled = True
            
            # Initialize default settings
            settings_to_create = [
                ('signup_enabled', str(default_signup_enabled), 'Whether new user registration is enabled', True),
            ]
            
            for key, value, description, is_editable in settings_to_create:
                existing = db_session.query(SystemSetting).filter_by(key=key).first()
                if not existing:
                    setting = SystemSetting(
                        key=key,
                        value=value,
                        description=description,
                        is_editable=is_editable
                    )
                    db_session.add(setting)
                    print(f"  ✓ Created setting: {key} = {value}")
                else:
                    print(f"  - Setting already exists: {key} = {existing.value}")
            
            db_session.commit()
            print("✓ System settings initialized successfully")
            
        except Exception as e:
            print(f"✗ Error initializing system settings: {e}")
            db_session.rollback()
        finally:
            db_session.close()
            
    except Exception as e:
        print(f"✗ Error updating database schema: {e}")
        return False
    
    print("\n✓ Database update completed successfully!")
    print("\nNew features added:")
    print("  - System settings table for configuration management")
    print("  - User access management for Mercury accounts") 
    print("  - Signup control (auto-disabled if users table is a view)")
    print("  - Admin interface for managing settings")
    
    return True

if __name__ == "__main__":
    success = update_database_schema()
    sys.exit(0 if success else 1)
