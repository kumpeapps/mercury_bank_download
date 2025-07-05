#!/usr/bin/env python3
"""
Reset user password for testing GUI
"""

import sys
import os

# Add the sync_app to the path
sys.path.append('/Users/justinkumpe/Documents/mercury_bank_download/sync_app')

# Import the required modules
from models.base import create_engine_and_session
from models.user import User
from werkzeug.security import generate_password_hash

def reset_user_password():
    """Reset the password for the 'test' user"""
    
    # Create database session
    engine, Session = create_engine_and_session()
    session = Session()
    
    try:
        # Find the test user
        user = session.query(User).filter_by(username='test').first()
        
        if user:
            # Set password to 'testpass123'
            new_password = 'testpass123'
            user.password_hash = generate_password_hash(new_password)
            session.commit()
            print(f"✓ Password for user '{user.username}' reset to '{new_password}'")
            return True
        else:
            print("✗ User 'test' not found")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("Resetting test user password...")
    reset_user_password()
