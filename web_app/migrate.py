#!/usr/bin/env python3
"""
Alembic Migration Helper Script
"""
import argparse
import os
import sys
import subprocess
from dotenv import load_dotenv

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def check_environment():
    """Check if the environment is properly configured."""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment. Please check your .env file.")
        return False
    
    print(f"✅ Database URL configured: {database_url.replace(database_url.split('@')[0].split('//')[1], '***:***')}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Alembic Migration Helper")
    parser.add_argument('action', choices=[
        'status', 'current', 'history', 'upgrade', 'downgrade', 
        'create', 'autogenerate', 'stamp', 'test-connection'
    ], help='Action to perform')
    parser.add_argument('--message', '-m', help='Migration message (for create/autogenerate)')
    parser.add_argument('--revision', '-r', help='Revision ID (for downgrade/stamp)')
    
    args = parser.parse_args()
    
    if not check_environment():
        sys.exit(1)
    
    if args.action == 'test-connection':
        # Inline database connection test
        from sqlalchemy import create_engine, text
        
        try:
            # Get database URL
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                print("❌ DATABASE_URL not found in environment")
                sys.exit(1)
            
            masked_url = database_url.replace(database_url.split('@')[0].split('//')[1], '***:***')
            print(f"Testing connection to: {masked_url}")
            
            # Create engine and test connection
            engine = create_engine(database_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                if row[0] == 1:
                    print("✅ Database connection successful!")
                    
                    # Check tables (database-agnostic way)
                    tables_result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()"))
                    tables = [row[0] for row in tables_result.fetchall()]
                    print(f"📋 Found {len(tables)} tables: {tables}")
                    sys.exit(0)
                else:
                    print("❌ Database connection test failed")
                    sys.exit(1)
                    
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)
    
    elif args.action == 'status' or args.action == 'current':
        run_command('alembic current', 'Checking current migration status')
    
    elif args.action == 'history':
        run_command('alembic history --verbose', 'Showing migration history')
    
    elif args.action == 'upgrade':
        run_command('alembic upgrade head', 'Upgrading database to latest migration')
    
    elif args.action == 'downgrade':
        if not args.revision:
            print("❌ Revision required for downgrade. Use --revision or -r")
            sys.exit(1)
        run_command(f'alembic downgrade {args.revision}', f'Downgrading database to {args.revision}')
    
    elif args.action == 'create':
        if not args.message:
            print("❌ Message required for creating migration. Use --message or -m")
            sys.exit(1)
        run_command(f'alembic revision -m "{args.message}"', f'Creating new migration: {args.message}')
    
    elif args.action == 'autogenerate':
        if not args.message:
            print("❌ Message required for autogenerate. Use --message or -m")
            sys.exit(1)
        run_command(f'alembic revision --autogenerate -m "{args.message}"', f'Auto-generating migration: {args.message}')
    
    elif args.action == 'stamp':
        if not args.revision:
            print("❌ Revision required for stamp. Use --revision or -r")
            sys.exit(1)
        run_command(f'alembic stamp {args.revision}', f'Stamping database with revision {args.revision}')

if __name__ == "__main__":
    main()
