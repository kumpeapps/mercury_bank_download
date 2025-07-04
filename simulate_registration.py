#!/usr/bin/env python3
"""
Test script to simulate the exact registration process
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
from models.user_settings import UserSettings

def simulate_registration():
    engine, Session = create_engine_and_session()
    db_session = Session()
    try:
        print("=== Simulating Registration Process ===")
        
        # Delete the existing user first to simulate fresh registration
        existing_user = db_session.query(User).filter_by(username='newuser').first()
        if existing_user:
            print("Deleting existing user for fresh test...")
            # Delete user settings first (due to foreign key)
            user_settings = db_session.query(UserSettings).filter_by(user_id=existing_user.id).first()
            if user_settings:
                db_session.delete(user_settings)
            # Clear roles
            existing_user.roles.clear()
            db_session.delete(existing_user)
            db_session.commit()
        
        # Now simulate the registration process exactly as in the code
        username = "testuser3"
        email = "testuser3@example.com"
        password = "testpass123"
        
        # Check if user already exists
        existing_user = db_session.query(User).filter_by(username=username).first()
        if existing_user:
            print("Username already exists")
            return
        
        # Check if this is the first user (should be admin)
        user_count = db_session.query(User).count()
        is_first_user = user_count == 0
        print(f"Current user count: {user_count}")
        print(f"Is first user: {is_first_user}")
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db_session.add(new_user)
        db_session.flush()  # Flush to get the user ID
        print(f"Created user with ID: {new_user.id}")
        
        # Assign roles to the new user
        print("Assigning roles...")
        
        # All users get the basic "user" role
        user_role = Role.get_or_create(db_session, "user", 
                                     "Basic user with read access to their own data", 
                                     is_system_role=True)
        print(f"User role: {user_role.name} (ID: {user_role.id})")
        new_user.roles.append(user_role)
        print(f"Roles after adding user role: {[r.name for r in new_user.roles]}")
        
        # If this is the first user, also grant admin and super-admin roles
        if is_first_user:
            admin_role = Role.get_or_create(db_session, "admin", 
                                          "Administrator with full system access", 
                                          is_system_role=True)
            super_admin_role = Role.get_or_create(db_session, "super-admin", 
                                                "Super administrator with all privileges including user management", 
                                                is_system_role=True)
            print(f"Admin role: {admin_role.name} (ID: {admin_role.id})")
            print(f"Super admin role: {super_admin_role.name} (ID: {super_admin_role.id})")
            
            new_user.roles.append(admin_role)
            new_user.roles.append(super_admin_role)
            print(f"Roles after adding admin roles: {[r.name for r in new_user.roles]}")
        
        # Create user settings
        user_settings = UserSettings(user_id=new_user.id)
        db_session.add(user_settings)
        print("Created user settings")
        
        # Commit everything
        print("Committing transaction...")
        db_session.commit()
        print("✅ Registration completed successfully!")
        
        # Verify the final state
        print("\n=== Verification ===")
        db_session.refresh(new_user)
        print(f"Final user roles: {[r.name for r in new_user.roles]}")
        
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        import traceback
        traceback.print_exc()
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == "__main__":
    simulate_registration()
