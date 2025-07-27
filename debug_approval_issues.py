#!/usr/bin/env python3
"""
Script to debug approval request status and email configuration.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project paths for imports
sys.path.append('/app')
sys.path.append('/app/models')

from models.system_setting import SystemSetting
from models.transaction_approval import TransactionApprovalRequest


def main():
    # Database connection
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://mercury_user:mercury_pass@localhost:3306/mercury_bank")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    
    try:
        print("🔍 Debugging approval system issues...")
        
        # Check approval requests and their status
        print("\n📋 Current approval requests:")
        requests = db_session.query(TransactionApprovalRequest).all()
        
        for req in requests:
            print(f"   ID: {req.id}, Status: '{req.status}' (type: {type(req.status).__name__})")
        
        # Check email-related system settings
        print("\n📧 Email configuration settings:")
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
        
        # Check environment variables for email
        print("\n🌍 Environment variables for email:")
        env_vars = [
            'SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD',
            'SMTP_FROM_EMAIL', 'SMTP_USE_TLS'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Hide password for security
                display_value = value if 'PASSWORD' not in var else '*****'
                print(f"   {var}: {display_value}")
            else:
                print(f"   {var}: NOT SET")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
