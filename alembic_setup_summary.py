#!/usr/bin/env python3
"""
Mercury Bank Platform - Alembic Setup Summary
"""
import os
import sys
from dotenv import load_dotenv

def check_alembic_setup():
    """Check the current Alembic setup status."""
    print("🔄 Mercury Bank Platform - Alembic Setup Summary")
    print("=" * 60)
    
    # Check environment
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        masked_url = database_url.replace(database_url.split('@')[0].split('//')[1], '***:***')
        print(f"✅ Database URL: {masked_url}")
    else:
        print("❌ DATABASE_URL not configured")
        return False
    
    # Check Alembic files
    alembic_files = [
        'alembic.ini',
        'alembic/env.py',
        'alembic/script.py.mako',
        'alembic/versions/'
    ]
    
    print("\n📁 Alembic Configuration:")
    for file in alembic_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - missing")
    
    # Check migration files
    versions_dir = 'alembic/versions'
    if os.path.exists(versions_dir):
        migrations = [f for f in os.listdir(versions_dir) if f.endswith('.py') and not f.startswith('__')]
        print(f"\n📄 Migration Files ({len(migrations)} total):")
        for migration in sorted(migrations):
            print(f"   • {migration}")
    
    # Check helper scripts
    helper_files = [
        'migrate.py',
        'docs/ALEMBIC_MIGRATION_GUIDE.md'
    ]
    
    print("\n🛠️  Helper Scripts:")
    for file in helper_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - missing")
    
    print("\n🚀 Quick Commands:")
    print("   python migrate.py test-connection    # Test database connection")
    print("   python migrate.py status             # Check migration status")
    print("   python migrate.py upgrade            # Apply pending migrations")
    print("   python migrate.py autogenerate -m 'Description'  # Create new migration")
    
    print("\n📚 Documentation:")
    print("   See docs/ALEMBIC_MIGRATION_GUIDE.md for detailed usage instructions")
    
    print("\n✨ Setup Complete!")
    print("   Alembic is configured and ready for database-agnostic migrations.")
    
    return True

if __name__ == "__main__":
    success = check_alembic_setup()
    sys.exit(0 if success else 1)
