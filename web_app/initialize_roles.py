#!/usr/bin/env python3
"""
Initialize system roles.

This script ensures that all standard system roles are created in the database.
It should be run during container startup to guarantee role availability.
"""

import os
import sys
from models.base import create_engine_and_session
from models.role import Role


def initialize_system_roles():
    """Initialize all standard system roles."""
    print("🔧 Initializing system roles...")
    
    # Define standard roles with descriptions
    standard_roles = [
        {
            "name": "user",
            "description": "Basic user with read access to their own data",
            "is_system_role": True
        },
        {
            "name": "admin", 
            "description": "Administrator with full system access",
            "is_system_role": True
        },
        {
            "name": "super-admin",
            "description": "Super administrator with all privileges including user management",
            "is_system_role": True
        },
        {
            "name": "reports",
            "description": "Access to generate and view reports",
            "is_system_role": True
        },
        {
            "name": "transactions",
            "description": "Access to view and manage transaction data",
            "is_system_role": True
        },
        {
            "name": "locked",
            "description": "Locked user with no system access",
            "is_system_role": True
        }
    ]
    
    try:
        engine, SessionLocal = create_engine_and_session()
        session = SessionLocal()
        
        created_count = 0
        for role_data in standard_roles:
            try:
                # Check if role exists
                existing_role = session.query(Role).filter_by(name=role_data["name"]).first()
                
                if not existing_role:
                    # Create new role
                    role = Role(
                        name=role_data["name"],
                        description=role_data["description"],
                        is_system_role=role_data["is_system_role"]
                    )
                    session.add(role)
                    created_count += 1
                    print(f"   ✅ Created role: {role_data['name']}")
                else:
                    # Update description if needed
                    if existing_role.description != role_data["description"]:
                        existing_role.description = role_data["description"]
                        print(f"   🔄 Updated description for role: {role_data['name']}")
                    else:
                        print(f"   ℹ️  Role already exists: {role_data['name']}")
                        
            except Exception as e:
                print(f"   ❌ Error processing role {role_data['name']}: {e}")
                session.rollback()
                continue
        
        # Commit all changes
        session.commit()
        
        if created_count > 0:
            print(f"✅ Successfully created {created_count} new roles")
        else:
            print("✅ All roles already exist - no changes needed")
            
        # Show final role count
        total_roles = session.query(Role).count()
        print(f"📊 Total roles in database: {total_roles}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing roles: {e}")
        if 'session' in locals():
            session.rollback()
        return False
        
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    print("Role Initialization Script")
    print("=" * 40)
    
    success = initialize_system_roles()
    
    if success:
        print("✅ Role initialization completed successfully")
        sys.exit(0)
    else:
        print("❌ Role initialization failed")
        sys.exit(1)
