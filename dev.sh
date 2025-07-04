#!/bin/bash

# Mercury Bank Local Development Helper Script
# This script helps with common development tasks

set -e

echo "Mercury Bank Local Development Helper"
echo "====================================="

# Function to show usage
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start          - Start all services with local MySQL"
    echo "  start-dev      - Start services in development mode (local builds)"
    echo "  stop           - Stop all services"
    echo "  rebuild-dev    - Stop services, rebuild images, and start in dev mode"
    echo "  logs           - Show logs from all services"
    echo "  logs-sync      - Show logs from sync service only"
    echo "  logs-web       - Show logs from web service only"
    echo "  logs-db        - Show logs from database only"
    echo "  build          - Build local images"
    echo "  clean          - Clean up containers and volumes"
    echo "  reset-db       - Reset local MySQL database (WARNING: deletes all data)"
    echo "  encrypt-keys   - Encrypt existing API keys"
    echo "  test-encrypt   - Test encryption functionality"
    echo ""
    echo "User Management:"
    echo "  first-admin    - Ensure first user has admin privileges"
    echo "  list-users     - List all users and their roles"
    echo "  user-count     - Show total number of users"
    echo "  promote-admin  - Promote a user to admin (requires username)"
    echo "  promote-super  - Promote a user to super-admin (requires username)"
    echo ""
    echo "Development:"
    echo "  shell-sync     - Open shell in sync container"
    echo "  shell-web      - Open shell in web container" 
    echo "  shell-db       - Open MySQL shell"
    echo "  cli-gui        - Launch text-based GUI for sync service"
    echo ""
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed or not in PATH"
    exit 1
fi

case "$1" in
    "start")
        echo "Starting Mercury Bank services with local MySQL..."
        docker-compose up -d
        echo "Services started. Access:"
        echo "  - Web App: http://localhost:5001"
        echo "  - Adminer: http://localhost:8080"
        echo "  - MySQL: localhost:3306"
        ;;
    
    "start-dev")
        echo "Starting Mercury Bank services in development mode..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
        echo "Development services started."
        ;;
    
    "stop")
        echo "Stopping Mercury Bank services..."
        docker-compose down
        ;;
    
    "rebuild-dev")
        echo "Rebuilding development services..."
        echo "Step 1: Stopping services..."
        docker-compose down
        
        echo "Step 2: Building images..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
        
        echo "Step 3: Starting services in development mode..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
        
        echo "✅ Development services rebuilt and started!"
        echo "Access:"
        echo "  - Web App: http://localhost:5001"
        echo "  - Adminer: http://localhost:8080"
        echo "  - MySQL: localhost:3306"
        ;;
    
    "logs")
        docker-compose logs -f
        ;;
    
    "logs-sync")
        docker-compose logs -f mercury-sync
        ;;
    
    "logs-web")
        docker-compose logs -f web-app
        ;;
    
    "logs-db")
        docker-compose logs -f mysql
        ;;
    
    "build")
        echo "Building local images..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
        ;;
    
    "clean")
        echo "Cleaning up containers and volumes..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        ;;
    
    "reset-db")
        echo "⚠️  WARNING: This will completely reset the local MySQL database!"
        echo "All data will be permanently lost."
        read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm
        
        if [ "$confirm" = "yes" ]; then
            echo "Stopping services..."
            docker-compose down
            
            echo "Removing MySQL data volume..."
            docker volume rm mercury_bank_download_mysql_data 2>/dev/null || echo "Volume not found (may already be deleted)"
            
            echo "Starting services with fresh database..."
            docker-compose up -d mysql
            
            echo "Waiting for MySQL to be ready..."
            sleep 10
            
            echo "Restarting services..."
            docker-compose up -d mercury-sync web-app
            
            echo "✅ Database reset complete!"
            echo "You can now register a new first user who will automatically become admin."
            echo "Or use './dev.sh first-admin' to promote the first existing user."
        else
            echo "Database reset cancelled."
        fi
        ;;
    
    "encrypt-keys")
        echo "Encrypting existing API keys..."
        docker-compose exec mercury-sync python encrypt_api_keys.py
        docker-compose exec web-app python encrypt_api_keys.py
        ;;
    
    "test-encrypt")
        echo "Testing encryption functionality..."
        docker-compose exec mercury-sync python test_encryption.py
        docker-compose exec web-app python test_encryption.py
        ;;
    
    "shell-sync")
        docker-compose exec mercury-sync /bin/bash
        ;;
    
    "shell-web")
        docker-compose exec web-app /bin/bash
        ;;
    
    "shell-db")
        docker-compose exec mysql mysql -u mercury_user -p mercury_bank
        ;;
    
    "cli-gui")
        echo "Launching text-based GUI for sync service..."
        docker-compose exec mercury-sync python cli_gui.py
        ;;
    
    "first-admin")
        echo "Ensuring first user has admin privileges..."
        docker-compose exec web-app python ensure_first_admin.py
        ;;
    
    "list-users")
        echo "Listing all users and their roles..."
        docker-compose exec web-app python -c "
import os
import sys
sys.path.append('/app')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User
from models.role import Role

database_url = os.environ.get('DATABASE_URL')
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

users = session.query(User).all()
print('\\nUsers and Roles:')
print('=' * 50)
for user in users:
    roles = [role.name for role in user.roles]
    roles_str = ', '.join(roles) if roles else 'No roles assigned'
    print(f'User: {user.username}')
    print(f'  Roles: {roles_str}')
    print(f'  Created: {user.created_at}')
    print()
session.close()
"
        ;;
    
    "user-count")
        echo "Checking user count..."
        docker-compose exec web-app python -c "
import os
import sys
sys.path.append('/app')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User

database_url = os.environ.get('DATABASE_URL')
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

count = session.query(User).count()
print(f'Total users in database: {count}')
session.close()
"
        ;;
    
    "promote-admin")
        if [ -z "$2" ]; then
            echo "Usage: $0 promote-admin <username>"
            exit 1
        fi
        echo "Promoting user '$2' to admin..."
        docker-compose exec web-app python -c "
import os
import sys
sys.path.append('/app')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User
from models.role import Role

database_url = os.environ.get('DATABASE_URL')
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

username = '$2'
user = session.query(User).filter_by(username=username).first()
if not user:
    print(f'User {username} not found')
    sys.exit(1)

admin_role = Role.get_or_create(session, 'admin')
user_role = Role.get_or_create(session, 'user')

if user_role not in user.roles:
    user.roles.append(user_role)
if admin_role not in user.roles:
    user.roles.append(admin_role)

session.commit()
print(f'User {username} promoted to admin')
session.close()
"
        ;;
    
    "promote-super")
        if [ -z "$2" ]; then
            echo "Usage: $0 promote-super <username>"
            exit 1
        fi
        echo "Promoting user '$2' to super-admin..."
        docker-compose exec web-app python -c "
import os
import sys
sys.path.append('/app')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User
from models.role import Role

database_url = os.environ.get('DATABASE_URL')
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

username = '$2'
user = session.query(User).filter_by(username=username).first()
if not user:
    print(f'User {username} not found')
    sys.exit(1)

user_role = Role.get_or_create(session, 'user')
admin_role = Role.get_or_create(session, 'admin')
super_admin_role = Role.get_or_create(session, 'super-admin')

if user_role not in user.roles:
    user.roles.append(user_role)
if admin_role not in user.roles:
    user.roles.append(admin_role)
if super_admin_role not in user.roles:
    user.roles.append(super_admin_role)

session.commit()
print(f'User {username} promoted to super-admin')
session.close()
"
        ;;
    
    *)
        show_usage
        exit 1
        ;;
esac
