#!/bin/bash

# Web app startup script with automatic migrations
# This script ensures database migrations are run before starting the Flask application

set -e  # Exit on any error

echo "🚀 Starting Mercury Bank Web Application..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if python -c "
import os
import mysql.connector
from mysql.connector import Error

database_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://user:password@db:3306/mercury_bank')

# Parse database URL
if database_url.startswith('mysql+pymysql://'):
    url = database_url.replace('mysql+pymysql://', '')
elif database_url.startswith('mysql://'):
    url = database_url.replace('mysql://', '')
else:
    exit(1)

try:
    auth_host, database = url.split('/', 1)
    auth, host_port = auth_host.split('@', 1)
    
    if ':' in auth:
        user, password = auth.split(':', 1)
    else:
        user = auth
        password = ''

    if ':' in host_port:
        host, port_str = host_port.split(':', 1)
        port = int(port_str)
    else:
        host = host_port
        port = 3306

    connection = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        connection_timeout=5,
        charset='utf8mb4',
        collation='utf8mb4_general_ci',
        use_unicode=True,
        auth_plugin='mysql_native_password'
    )
    connection.close()
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

# Run database migrations
echo "� Running database migrations..."
if python migration_manager.py; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Database migrations failed"
    exit 1
fi

# Start the Flask application
echo "🌐 Starting Flask application..."
exec python app.py
