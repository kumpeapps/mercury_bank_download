#!/usr/bin/env python3
"""
Test script to manually assign roles to first user
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

def assign_roles_to_first_user():
    engine, Session = create_engine_and_session()
    db_session = Session()
    try:
        # Get the first user
        first_user = db_session.query(User).first()
        if not first_user:
            print("No users found!")
            return
            
        print(f"First user: {first_user.username} (ID: {first_user.id})")
        print(f"Current roles: {[role.name for role in first_user.roles]}")
        
        # Get or create required roles
        user_role = Role.get_or_create(db_session, "user", 
                                     "Basic user with read access to their own data", 
                                     is_system_role=True)
        admin_role = Role.get_or_create(db_session, "admin", 
                                      "Administrator with full system access", 
                                      is_system_role=True)
        super_admin_role = Role.get_or_create(db_session, "super-admin", 
                                            "Super administrator with all privileges including user management", 
                                            is_system_role=True)
        
        print(f"Retrieved roles: user={user_role.id}, admin={admin_role.id}, super-admin={super_admin_role.id}")
        
        # Clear existing roles first
        first_user.roles.clear()
        
        # Assign roles
        first_user.roles.append(user_role)
        first_user.roles.append(admin_role)
        first_user.roles.append(super_admin_role)
        
        print(f"Assigned roles: {[role.name for role in first_user.roles]}")
        
        # Commit changes
        db_session.commit()
        print("✅ Roles assigned successfully!")
        
        # Verify assignment
        db_session.refresh(first_user)
        print(f"Final roles: {[role.name for role in first_user.roles]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == "__main__":
    assign_roles_to_first_user()
