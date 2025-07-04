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

# Create database schema using SQLAlchemy
echo "🔄 Creating/updating database schema..."

if python -c "
from models.base import Base
from sqlalchemy import create_engine
import os

database_url = os.environ.get('DATABASE_URL')
engine = create_engine(database_url)
Base.metadata.create_all(engine)
print('Database schema created/updated successfully')
"; then
    echo "✅ Database schema ready"
else
    echo "❌ Database schema creation failed"
    exit 1
fi

# Ensure super admin user is promoted (if specified)
echo "👑 Checking super admin user..."
python ensure_super_admin.py

# Start the sync service
echo "🔄 Starting sync service..."
exec python sync.py
