#!/usr/bin/env python3
"""
Script to add missing smtp_from_email setting.
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
        print("🔧 Adding missing smtp_from_email setting...")
        
        # Check if smtp_from_email exists
        smtp_from = db_session.query(SystemSetting).filter_by(key='smtp_from_email').first()
        if not smtp_from:
            # Use the same email as smtp_username as the from email
            smtp_username = SystemSetting.get_value(db_session, 'smtp_username')
            
            smtp_from = SystemSetting(
                key='smtp_from_email',
                value=smtp_username,  # Use same email as username
                description='From email address for SMTP notifications',
                is_editable=True
            )
            db_session.add(smtp_from)
            db_session.commit()
            print(f"   ✅ Added smtp_from_email: {smtp_username}")
        else:
            print(f"   ℹ️  smtp_from_email already exists: {smtp_from.value}")
            
        # Verify all email settings now
        print("\n📧 Updated email configuration:")
        email_settings = [
            'smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 
            'smtp_from_email', 'smtp_use_tls', 'approval_email_enabled'
        ]
        
        for setting_key in email_settings:
            setting = db_session.query(SystemSetting).filter_by(key=setting_key).first()
            if setting:
                # Hide password for security
                value = setting.value if 'password' not in setting_key else '*****'
                print(f"   {setting_key}: {value}")
            else:
                print(f"   {setting_key}: NOT FOUND")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db_session.rollback()
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
