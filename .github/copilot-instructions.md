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
   - Database migrations should be done through SQLAlchemy-based migration scripts
   - Migrations run automatically at container startup and should be idempotent

2. **Security Considerations**
   - API keys must be encrypted at rest using the encryption utilities
   - User authentication follows secure practices
   - User inputs must be validated and sanitized

3. **Admin Features**
   - First user is automatically an admin
   - SUPER_ADMIN_USERNAME environment variable defines a user that always has admin privileges
   - System settings control features like user registration and user deletion

4. **Docker Deployment**
   - Local development uses docker-compose with MySQL
   - Production deployment uses pre-built images
   - Health checks are implemented for all services
   - ALWAYS use `./dev.sh rebuild-dev` instead of `docker restart` to apply changes
   - Never use individual container restarts like `docker restart container-name`

5. **Code Structure**
   - Models are defined in both sync_app/models/ and web_app/models/
   - Both apps share the same database schema
   - Changes to one model directory should be replicated in the other

## Common Tasks

- **Add New Model**: Define in both sync_app/models/ and web_app/models/
- **Database Changes**: Implement via SQLAlchemy migrations
- **Admin Settings**: Add to SystemSetting initialization in app.py
- **API Key Management**: Use the encryption utilities for secure storage
- **Applying Changes**: Always use `./dev.sh rebuild-dev` to rebuild and restart services

## Development Workflow
Use the `dev.sh` script for common development tasks such as:
- Starting/stopping services: `./dev.sh start-dev`, `./dev.sh stop`
- Building images: Use `./dev.sh rebuild-dev` to rebuild and restart development environment
- Running migrations: Migrations run automatically at container startup
- Resetting the database: `./dev.sh reset-db`
- Managing users and roles: 
  - `./dev.sh assign-role <username> <role>` - Assign roles to users
  - `./dev.sh list-by-role <role>` - List users with specific roles
  - `./dev.sh list-roles` - List all available roles
  - `./dev.sh create-role` - Create new roles
  - Legacy commands still supported: `./dev.sh promote-admin`, `./dev.sh demote-admin`

### Migration Guidelines
- Migrations are performed automatically when containers start
- Use the existing SQLAlchemy-based migration structure in both `web_app/migrations/` and `sync_app/migrations/`
- Create migration files with descriptive names following the pattern: `XXX_description.py`
- Include both `upgrade()` and `downgrade()` functions in migration files
- Add column existence checks to make migrations idempotent and safe for re-runs
- Migrations should use SQLAlchemy and avoid raw SQL when possible
- Always test migrations in development using `./dev.sh rebuild-dev`
