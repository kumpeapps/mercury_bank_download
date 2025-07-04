#!/usr/bin/env python3
"""
Test script to debug first user role assignment
"""
import os
import sys

# Add the web app directory to Python path
sys.path.insert(0, '/app')

# Set database URL
os.environ['DATABASE_URL'] = 'mysql+pymysql://mercury_user:mercury_password@mysql:3306/mercury_bank'

from models.base import create_engine_and_session
from models.user import User
from models.role import Role

def test_first_user_logic():
    engine, Session = create_engine_and_session()
    db_session = Session()
    try:
        # Check user count
        user_count = db_session.query(User).count()
        print(f"Total users: {user_count}")
        
        # Get the first user
        first_user = db_session.query(User).first()
        if first_user:
            print(f"First user: {first_user.username} (ID: {first_user.id})")
            print(f"User roles: {[role.name for role in first_user.roles]}")
        
        # Check all roles
        all_roles = db_session.query(Role).all()
        print(f"Available roles: {[role.name for role in all_roles]}")
        
        # Check if first user was created when user_count was 0
        print(f"Should be first user: {user_count == 1}")  # If there's 1 user now, it was 0 when created
        
    finally:
        db_session.close()

if __name__ == "__main__":
    test_first_user_logic()
