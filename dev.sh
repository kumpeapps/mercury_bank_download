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
    echo "  migrate        - Run database migrations"
    echo "  encrypt-keys   - Encrypt existing API keys"
    echo "  test-encrypt   - Test encryption functionality"
    echo ""
    echo "Admin Management:"
    echo "  create-admin   - Create first admin user"
    echo "  promote-admin  - Promote existing user to admin"
    echo "  demote-admin   - Remove admin privileges from a user"
    echo "  list-admin     - List all admin users"
    echo "  ensure-admin   - Ensure first user is admin (migration)"
    echo "  add-user       - Create a new user account"
    echo "  delete-user    - Delete a user account"
    echo "  list-users     - List all users"
    echo "  toggle-signup  - Enable/disable user registration"
    echo "  toggle-user-deletion - Enable/disable prevention of user deletion"
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
            
            echo "Running migrations..."
            docker-compose up -d mercury-sync web-app
            
            echo "✅ Database reset complete!"
            echo "You can now register a new first user who will automatically become admin."
        else
            echo "Database reset cancelled."
        fi
        ;;
    
    "migrate")
        echo "Running database migrations..."
        docker-compose exec mercury-sync python setup_db.py
        docker-compose exec web-app python migration_manager.py
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
    
    "create-admin")
        echo "Creating first admin user..."
        docker-compose exec web-app python admin_user.py create
        ;;
    
    "promote-admin")
        if [ -z "$2" ]; then
            echo "Usage: $0 promote-admin <username>"
            exit 1
        fi
        echo "Promoting user '$2' to admin..."
        docker-compose exec web-app python admin_user.py promote "$2"
        ;;
    
    "demote-admin")
        if [ -z "$2" ]; then
            echo "Usage: $0 demote-admin <username>"
            exit 1
        fi
        echo "Removing admin privileges from user '$2'..."
        docker-compose exec web-app python admin_user.py demote "$2"
        ;;
    
    "list-admin")
        echo "Listing admin users..."
        docker-compose exec web-app python admin_user.py list_admin
        ;;
    
    "ensure-admin")
        echo "Ensuring first user is admin..."
        docker-compose exec web-app python ensure_first_admin.py
        ;;
    
    "add-user")
        echo "Creating a new user account..."
        docker-compose exec web-app python admin_user.py add
        ;;
    
    "delete-user")
        if [ -z "$2" ]; then
            echo "Usage: $0 delete-user <username>"
            exit 1
        fi
        echo "Deleting user account '$2'..."
        docker-compose exec web-app python admin_user.py delete "$2"
        ;;
    
    "list-users")
        echo "Listing all users..."
        docker-compose exec web-app python admin_user.py list
        ;;
    
    "toggle-signup")
        echo "Toggling user registration..."
        docker-compose exec web-app python admin_user.py toggle_signup
        ;;
    
    "toggle-user-deletion")
        echo "Toggling user deletion prevention..."
        docker-compose exec web-app python admin_user.py toggle_user_deletion
        ;;
    
    "shell-sync")
        docker-compose exec mercury-sync /bin/bash
        ;;
    
    "shell-web")
        docker-compose exec web-app /bin/bash
        ;;
    
    "shell-db")
        docker-compose exec mysql mysql -u mercury_user -p mercury_db
        ;;
    
    *)
        show_usage
        exit 1
        ;;
esac
