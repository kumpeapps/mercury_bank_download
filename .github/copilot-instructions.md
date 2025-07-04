# GitHub Copilot Instructions for Mercury Bank Integration Platform

## Project Overview
This is a Mercury Bank Integration Platform consisting of two main components:
1. **Sync Service** (`sync_app/`) - Automated data synchronization from Mercury Bank API
2. **Web Interface** (`web_app/`) - User-friendly web dashboard for data management and reporting

## Key Technologies
- **Python**: Primary programming language
- **Flask**: Web framework for the web interface
- **SQLAlchemy**: ORM for all database interactions
- **Docker**: Containerization for deployment
- **MySQL**: Database backend

## Important Guidelines

1. **Use SQLAlchemy for all database operations**
   - All database operations MUST use SQLAlchemy ORM
   - Do NOT use raw SQL or .sql files for schema changes or data modifications
   - Database schema is created using SQLAlchemy's `create_all()` method
   - Schema creation runs automatically at container startup

2. **Security Considerations**
   - API keys must be encrypted at rest using the encryption utilities
   - User authentication follows secure practices
   - User inputs must be validated and sanitized

3. **Role-Based Access Control**
   - Use the role-based system for all user management
   - Legacy admin features (is_admin flag, promote/demote commands) are DEPRECATED
   - Users must have appropriate roles: "user", "admin", "super-admin", etc.
   - Use role management interface and commands for user permissions

4. **Admin Features**
   - First user is automatically an admin
   - SUPER_ADMIN_USERNAME environment variable defines a user that always has admin privileges
   - System settings control features like user registration and user deletion

5. **Docker Deployment**
   - Local development uses docker-compose with MySQL
   - Production deployment uses pre-built images
   - Health checks are implemented for all services
   - ALWAYS use `./dev.sh rebuild-dev` instead of `docker restart` to apply changes
   - Never use individual container restarts like `docker restart container-name`

6. **Code Structure**
   - Models are defined in both sync_app/models/ and web_app/models/
   - Both apps share the same database schema
   - Changes to one model directory should be replicated in the other

7. **Legacy Features - DEPRECATED**
   - Legacy admin_user.py scripts have been archived
   - MERCURY_API_KEY environment variable is no longer used (API keys stored in database)
   - Legacy promote-admin, demote-admin, list-admin commands removed
   - Use role-based system instead of is_admin flag for new development

## Common Tasks

- **Add New Model**: Define in both sync_app/models/ and web_app/models/
- **Database Changes**: Implement via SQLAlchemy model changes and rebuild containers
- **Admin Settings**: Add to SystemSetting initialization in app.py
- **API Key Management**: Use the encryption utilities for secure storage
- **Applying Changes**: Always use `./dev.sh rebuild-dev` to rebuild and restart services

## Development Workflow
Use the `dev.sh` script for common development tasks such as:
- Starting/stopping services: `./dev.sh start-dev`, `./dev.sh stop`
- Building images: Use `./dev.sh rebuild-dev` to rebuild and restart development environment
- Running schemas: Schema creation runs automatically at container startup
- Resetting the database: `./dev.sh reset-db`
- Managing users and roles: 
  - `./dev.sh assign-role <username> <role>` - Assign roles to users
  - `./dev.sh remove-role <username> <role>` - Remove roles from users
  - `./dev.sh list-by-role <role>` - List users with specific roles
  - `./dev.sh list-roles` - List all available roles
  - `./dev.sh create-role` - Create new roles
  - `./dev.sh add-user` - Add new users with role selection
  - `./dev.sh list-users` - List all users and their roles

### Schema Creation Guidelines
- Schema creation is performed automatically when containers start
- Uses SQLAlchemy's `create_all()` method for automatic schema creation
- Model changes require container rebuild using `./dev.sh rebuild-dev`
- Schema changes should be made to SQLAlchemy model definitions
- Always test schema changes in development using `./dev.sh rebuild-dev`
