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
   - Users must have appropriate roles: "user", "admin", "super-admin", etc.
   - All permissions are managed through the role system

4. **Admin Features**
   - First user is automatically assigned admin and super-admin roles
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
- User and role management: Use the web interface at `/admin/users` for all user and role management tasks

### Schema Creation Guidelines
- Schema creation is performed automatically when containers start
- Uses SQLAlchemy's `create_all()` method for automatic schema creation
- Model changes require container rebuild using `./dev.sh rebuild-dev`
- Schema changes should be made to SQLAlchemy model definitions
- Always test schema changes in development using `./dev.sh rebuild-dev`

## Testing Framework

### Test Structure
The platform includes a comprehensive test suite located in the `tests/` directory:
- **Unit Tests** (`test_models.py`) - Database model validation and relationships
- **Integration Tests** (`test_user_registration.py`) - User registration and role assignment logic
- **Web Tests** (`test_web_integration.py`) - HTTP endpoints, authentication, and form processing

### Running Tests
Use the test runner script for all testing needs:
```bash
./run_tests.sh                    # Run all tests with coverage
./run_tests.sh --no-coverage      # Run tests without coverage
./run_tests.sh --verbose          # Verbose output
./run_tests.sh --pattern="test_*" # Run specific test patterns
```

### Test Categories and Coverage

#### Model Tests (17 test cases)
- User model creation and password handling
- Role-based permissions and relationships
- User settings without legacy fields (no is_admin flag)
- System settings initialization and value handling
- Mercury account and transaction model relationships

#### User Registration Tests (9 test cases)
- **First user automatically gets admin roles**: admin, super-admin, and user
- **Subsequent users get only user role**: enforces proper role hierarchy
- Password hashing and authentication validation
- Username uniqueness enforcement
- User settings creation and association

#### Web Integration Tests (12 test cases)
- **Registration workflow**: Page loading, form submission, validation
- **Authentication flow**: Login success/failure, session management
- **Permission enforcement**: Role-based access control
- **Protected routes**: Dashboard requires authentication
- **System settings**: Registration can be disabled dynamically
- **Error handling**: Duplicate users, invalid credentials

### Test Database Configuration
- Uses SQLite in-memory database for isolation
- Separate test Flask app with minimal templates
- Fixtures for roles, system settings, and clean database state
- No dependency on production MySQL database

### Key Test Validations
- **Role Assignment Logic**: First user gets all admin roles, others get user role only
- **Authentication Security**: Password hashing, login validation, session management
- **Permission System**: Role-based access control without legacy is_admin flags
- **Error Handling**: Proper validation and error messages for edge cases
- **Database Integrity**: Model relationships and constraints work correctly

### CI/CD Integration
- GitHub Actions workflow runs all tests automatically
- Matrix testing across Python versions
- Docker integration tests
- Security scanning with safety and bandit
- Coverage reporting with minimum thresholds

### Test Development Guidelines
- All new features should include corresponding tests
- Test both happy path and error conditions
- Use descriptive test names that explain the scenario
- Follow the existing fixture pattern for database setup
- Ensure tests are isolated and don't depend on each other
