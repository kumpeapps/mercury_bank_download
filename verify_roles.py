#!/usr/bin/env python3

import sys
import os
sys.path.append('sync_app')

# Import SQLAlchemy and database utilities
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = "mysql+pymysql://mercury_user:mercury_password@localhost:3306/mercury_bank"

def verify_roles():
    """Verify all roles exist in database"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Query roles directly using SQL
        result = session.execute(text("SELECT name, is_system_role FROM roles ORDER BY name"))
        roles = result.fetchall()
        
        print(f"📊 Total roles in database: {len(roles)}")
        print("\n🔍 Role details:")
        for role in roles:
            system_indicator = "✅" if role.is_system_role else "❌"
            print(f"  {system_indicator} {role.name} (system_role: {role.is_system_role})")
        
        # Check if transactions and reports roles exist
        role_names = [role.name for role in roles]
        missing_roles = []
        expected_roles = ['user', 'admin', 'super-admin', 'transactions', 'reports', 'locked']
        
        for expected in expected_roles:
            if expected not in role_names:
                missing_roles.append(expected)
        
        if missing_roles:
            print(f"\n❌ Missing roles: {missing_roles}")
            return False
        else:
            print(f"\n✅ All expected roles are present!")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying roles: {str(e)}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    verify_roles()
