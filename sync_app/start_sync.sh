#!/bin/bash

# Main app startup script using SQLAlchemy only
# This script creates the database schema and starts the sync process

set -e  # Exit on any error

echo "🚀 Starting Mercury Bank Sync Service..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if python -c "
import os
from sqlalchemy import create_engine, text

database_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://user:password@db:3306/mercury_bank')

try:
    engine = create_engine(database_url, connect_args={'connect_timeout': 5})
    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))
    print('Database connection successful')
    exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"; then
        echo "✅ Database is ready!"
        break
    else
        echo "🔄 Database not ready, attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Database connection failed after $max_attempts attempts"
    exit 1
fi

# Run database migrations using Alembic
echo "🔄 Running database migrations..."

# Check if alembic_version table exists (indicates if migrations have been run)
if python -c "
from sqlalchemy import create_engine, text
import os

database_url = os.environ.get('DATABASE_URL')
engine = create_engine(database_url)

try:
    with engine.connect() as conn:
        result = conn.execute(text('SHOW TABLES LIKE \"alembic_version\"'))
        tables = result.fetchall()
        if len(tables) > 0:
            print('Migration table exists')
            exit(0)
        else:
            print('Migration table does not exist')
            exit(1)
except Exception as e:
    print(f'Error checking migration table: {e}')
    exit(1)
"; then
    echo "� Migration table exists, running upgrade..."
    if python migrate.py upgrade; then
        echo "✅ Database migrations completed"
    else
        echo "❌ Database migration failed"
        exit 1
    fi
else
    echo "🆕 First run detected, creating schema and stamping with latest migration..."
    # For fresh installs, create the schema first, then stamp with latest migration
    if python -c "
from models.base import Base
from sqlalchemy import create_engine
import os

database_url = os.environ.get('DATABASE_URL')
engine = create_engine(database_url)
Base.metadata.create_all(engine)
print('Database schema created successfully')
"; then
        echo "✅ Schema created, now stamping with latest migration..."
        # Get the latest revision ID dynamically
        latest_revision=$(python migrate.py history | head -1 | cut -d':' -f1 | cut -d' ' -f2)
        if python migrate.py stamp --revision "$latest_revision"; then
            echo "✅ Database stamped with latest migration"
        else
            echo "❌ Failed to stamp database with migration"
            exit 1
        fi
    else
        echo "❌ Database schema creation failed"
        exit 1
    fi
fi

# Initialize system roles
echo "🔧 Initializing system roles..."
if python initialize_roles.py; then
    echo "✅ System roles initialized"
else
    echo "❌ Role initialization failed"
    exit 1
fi

# Ensure super admin user is promoted (if specified)
echo "👑 Checking super admin user..."
python ensure_super_admin.py

# Start the sync service
echo "🔄 Starting sync service..."
exec python sync.py
