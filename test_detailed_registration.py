#!/usr/bin/env python3
"""
Comprehensive test of first user registration with detailed logging
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

def test_complete_registration_flow():
    engine, Session = create_engine_and_session()
    db_session = Session()
    
    try:
        print("=== Testing Complete Registration Flow ===")
        
        # 1. Check initial state
        print("\n1. Initial Database State:")
        user_count = db_session.query(User).count()
        role_count = db_session.query(Role).count()
        print(f"   Users: {user_count}")
        print(f"   Roles: {role_count}")
        
        # 2. Simulate the EXACT registration process from web app
        print("\n2. Starting Registration Process:")
        username = "firstuser"
        email = "firstuser@example.com"
        password = "firstpass123"
        
        # Check if user already exists
        existing_user = db_session.query(User).filter_by(username=username).first()
        if existing_user:
            print(f"   ❌ Username {username} already exists")
            return
        print(f"   ✅ Username {username} is available")
        
        # Check if this is the first user (should be admin)
        user_count = db_session.query(User).count()
        is_first_user = user_count == 0
        print(f"   📊 Current user count: {user_count}")
        print(f"   🎯 Is first user: {is_first_user}")
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db_session.add(new_user)
        db_session.flush()  # Flush to get the user ID
        print(f"   👤 Created user with ID: {new_user.id}")
        
        # Assign roles to the new user - TEST EACH STEP
        print("\n3. Role Assignment Process:")
        
        # All users get the basic "user" role
        print("   3a. Assigning 'user' role:")
        user_role = Role.get_or_create(db_session, "user", 
                                     "Basic user with read access to their own data", 
                                     is_system_role=True)
        print(f"      Role object: {user_role} (ID: {user_role.id})")
        
        # Before appending
        print(f"      Roles before append: {[r.name for r in new_user.roles]}")
        new_user.roles.append(user_role)
        print(f"      Roles after append: {[r.name for r in new_user.roles]}")
        
        # If this is the first user, also grant admin and super-admin roles
        if is_first_user:
            print("   3b. Assigning 'admin' role:")
            admin_role = Role.get_or_create(db_session, "admin", 
                                          "Administrator with full system access", 
                                          is_system_role=True)
            print(f"      Role object: {admin_role} (ID: {admin_role.id})")
            new_user.roles.append(admin_role)
            print(f"      Roles after admin append: {[r.name for r in new_user.roles]}")
            
            print("   3c. Assigning 'super-admin' role:")
            super_admin_role = Role.get_or_create(db_session, "super-admin", 
                                                "Super administrator with all privileges including user management", 
                                                is_system_role=True)
            print(f"      Role object: {super_admin_role} (ID: {super_admin_role.id})")
            new_user.roles.append(super_admin_role)
            print(f"      Roles after super-admin append: {[r.name for r in new_user.roles]}")
        else:
            print("   3b-c. Skipping admin roles (not first user)")
        
        # Create user settings
        print("\n4. Creating User Settings:")
        user_settings = UserSettings(user_id=new_user.id)
        db_session.add(user_settings)
        print(f"   ✅ User settings created for user ID: {new_user.id}")
        
        # Pre-commit verification
        print("\n5. Pre-commit Verification:")
        print(f"   User roles: {[r.name for r in new_user.roles]}")
        print(f"   Session dirty objects: {list(db_session.dirty)}")
        print(f"   Session new objects: {list(db_session.new)}")
        
        # Commit everything
        print("\n6. Committing Transaction:")
        db_session.commit()
        print("   ✅ Transaction committed successfully!")
        
        # Post-commit verification
        print("\n7. Post-commit Verification:")
        db_session.refresh(new_user)
        print(f"   Final user roles: {[r.name for r in new_user.roles]}")
        
        # Verify in database directly
        print("\n8. Database Verification:")
        user_check = db_session.query(User).filter_by(username=username).first()
        if user_check:
            print(f"   User found: {user_check.username} (ID: {user_check.id})")
            print(f"   Roles from DB: {[r.name for r in user_check.roles]}")
        else:
            print("   ❌ User not found in database!")
        
        # Check role assignments in user_roles table
        from sqlalchemy import text
        result = db_session.execute(text("""
            SELECT u.username, r.name as role_name 
            FROM users u 
            LEFT JOIN user_roles ur ON u.id = ur.user_id 
            LEFT JOIN roles r ON ur.role_id = r.id 
            WHERE u.username = :username
        """), {'username': username})
        
        print("   Role assignments in database:")
        for row in result:
            print(f"      {row.username} -> {row.role_name}")
        
        print("\n✅ Registration test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during registration: {e}")
        import traceback
        traceback.print_exc()
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == "__main__":
    test_complete_registration_flow()
