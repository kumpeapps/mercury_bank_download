#!/usr/bin/env python3
"""
Script to enable approval notification settings.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project paths for imports
sys.path.append('/app')
sys.path.append('/app/models')

from models.system_setting import SystemSetting


def main():
    # Database connection
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://mercury_user:mercury_pass@localhost:3306/mercury_bank")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    
    try:
        print("🔧 Enabling approval notification settings...")
        
        # Enable email notifications
        email_setting = db_session.query(SystemSetting).filter_by(key='approval_email_enabled').first()
        if email_setting:
            email_setting.value = "true"
            print(f"   ✅ Email notifications: {email_setting.value}")
        else:
            print("   ❌ Email setting not found")
        
        # Enable Pushover notifications  
        pushover_setting = db_session.query(SystemSetting).filter_by(key='approval_pushover_enabled').first()
        if pushover_setting:
            pushover_setting.value = "true"
            print(f"   ✅ Pushover notifications: {pushover_setting.value}")
        else:
            print("   ❌ Pushover setting not found")
        
        db_session.commit()
        print("✅ Notification settings updated successfully!")
        
        # Show current settings
        print("\n📋 Current notification settings:")
        settings = db_session.query(SystemSetting).filter(
            SystemSetting.key.in_(['approval_email_enabled', 'approval_pushover_enabled'])
        ).all()
        
        for setting in settings:
            print(f"   {setting.key}: {setting.value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db_session.rollback()
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
