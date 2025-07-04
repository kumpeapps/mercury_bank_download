# Mercury Bank Integration Platform - Testing Guide

This document describes the comprehensive testing suite for the Mercury Bank Integration Platform.

## Overview

The test suite is designed to ensure the reliability and correctness of the platform, particularly focusing on:

- ✅ **User Registration & Role Assignment** - Critical security functionality
- ✅ **Database Models & Relationships** - Data integrity and ORM functionality  
- ✅ **Web Interface Integration** - End-to-end user workflows
- ✅ **Authentication & Authorization** - Security and access control
- ✅ **System Settings** - Configuration management

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                # Pytest fixtures and configuration
├── test_user_registration.py  # User registration and role tests
├── test_models.py             # Database model tests
└── test_web_integration.py    # Web application integration tests
```

## Running Tests

### Quick Start

```bash
# Run all tests with coverage
./run_tests.sh

# Run specific test types
./run_tests.sh --unit           # Unit tests only
./run_tests.sh --integration    # Integration tests only
./run_tests.sh --models         # Model tests only

# Run with specific options
./run_tests.sh --verbose --parallel --no-coverage
```

### Manual Test Execution

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Set environment variables
export PYTHONPATH="web_app:sync_app:$PYTHONPATH"
export TEST_DATABASE_URL="sqlite:///:memory:"

# Run tests
pytest tests/ -v --cov=web_app --cov=sync_app
```

### Test Options

| Option | Description |
|--------|-------------|
| `--unit` | Run only unit tests (fast, isolated) |
| `--integration` | Run only integration tests (slower, end-to-end) |
| `--models` | Run only database model tests |
| `--verbose` | Detailed test output |
| `--parallel` | Run tests in parallel for speed |
| `--no-coverage` | Skip coverage reporting |
| `--pattern "test_name"` | Run tests matching pattern |

## Test Categories

### 1. User Registration Tests (`test_user_registration.py`)

**Critical Functionality:** Ensures the first user becomes admin and subsequent users get appropriate roles.

- ✅ First user gets `user`, `admin`, and `super-admin` roles
- ✅ Subsequent users get only `user` role  
- ✅ User settings creation without legacy `is_admin` field
- ✅ Password hashing and verification
- ✅ Username uniqueness enforcement
- ✅ Role assignment and permission checking

### 2. Database Model Tests (`test_models.py`)

**Data Integrity:** Validates all SQLAlchemy models and relationships.

- ✅ User model creation and relationships
- ✅ Role model and `get_or_create` functionality
- ✅ UserSettings model without legacy fields
- ✅ SystemSetting model and helper methods
- ✅ MercuryAccount and Account models
- ✅ Model relationships and foreign keys

### 3. Web Integration Tests (`test_web_integration.py`)

**End-to-End Testing:** Validates complete user workflows through the web interface.

- ✅ Registration page accessibility
- ✅ First user registration via web (gets admin roles)
- ✅ Subsequent user registration via web (gets user role)
- ✅ Login/logout functionality
- ✅ Authentication requirements for protected pages
- ✅ Permission enforcement for different user types
- ✅ System settings integration

## Database Testing

### Test Database Configuration

Tests use an in-memory SQLite database by default for speed and isolation:

```python
TEST_DATABASE_URL = "sqlite:///:memory:"
```

For integration testing with MySQL (matching production):

```bash
export TEST_DATABASE_URL="mysql+pymysql://user:pass@localhost:3306/test_db"
```

### Test Fixtures

Key fixtures provided in `conftest.py`:

- `test_db` - Clean database session for each test
- `test_app` - Flask test client
- `init_roles` - Standard system roles
- `init_system_settings` - Default system settings

## Continuous Integration

### GitHub Actions Workflow

The platform includes a comprehensive GitHub Actions workflow (`.github/workflows/test.yml`) that:

1. **Matrix Testing** - Tests against Python 3.9, 3.10, 3.11
2. **Service Testing** - Tests with real MySQL database
3. **Docker Testing** - Validates complete Docker deployment
4. **Security Scanning** - Runs Bandit and Safety security checks
5. **Coverage Reporting** - Generates and uploads coverage reports

### Workflow Triggers

- ✅ Push to `main` or `develop` branches
- ✅ Pull requests to `main` or `develop`
- ✅ Manual workflow dispatch
- ✅ Scheduled runs (optional)

### Docker Integration Testing

The workflow includes Docker-based testing that:

1. Builds all Docker images
2. Starts the complete platform stack
3. Tests user registration flow end-to-end
4. Verifies database role assignments
5. Checks service health endpoints

## Local Development Testing

### Pre-commit Testing

Before committing changes:

```bash
# Quick validation
./run_tests.sh --unit

# Full test suite
./run_tests.sh --verbose

# Test specific functionality
./run_tests.sh --pattern "test_registration"
```

### Integration with Development Workflow

The tests integrate with the development workflow:

```bash
# After making changes, rebuild and test
./dev.sh rebuild-dev
./run_tests.sh --integration

# Test specific scenarios
./run_tests.sh --pattern "first_user"
```

## Coverage Requirements

The test suite maintains high coverage standards:

- **Minimum Coverage:** 80%
- **Target Coverage:** 90%+
- **Critical Paths:** 100% (user registration, authentication)

Coverage reports are generated in `htmlcov/index.html`.

## Adding New Tests

### Test Structure Guidelines

1. **Test Names:** Use descriptive names starting with `test_`
2. **Test Classes:** Group related tests in classes starting with `Test`
3. **Fixtures:** Use appropriate fixtures from `conftest.py`
4. **Assertions:** Use clear, specific assertions
5. **Documentation:** Add docstrings explaining test purpose

### Example Test

```python
def test_new_functionality(test_db, init_roles):
    """Test description of what this validates."""
    # Arrange
    user = User(username="testuser", email="test@example.com")
    test_db.add(user)
    test_db.flush()
    
    # Act
    result = user.some_method()
    
    # Assert
    assert result is not None
    assert user.has_expected_property()
```

## Troubleshooting

### Common Issues

1. **Import Errors:** Ensure `PYTHONPATH` includes `web_app` and `sync_app`
2. **Database Errors:** Check `TEST_DATABASE_URL` configuration
3. **Port Conflicts:** Ensure test ports (5001, 3306) are available
4. **Permission Errors:** Check file permissions on test scripts

### Debug Mode

Run tests with extra debugging:

```bash
./run_tests.sh --verbose --pattern "failing_test" --no-coverage
```

### Manual Database Inspection

For integration tests with persistent database:

```bash
export TEST_DATABASE_URL="mysql+pymysql://user:pass@localhost:3306/test_db"
./run_tests.sh --integration
# Database remains for inspection
```

## Security Testing

The test suite includes security validations:

- ✅ Password hashing verification
- ✅ SQL injection prevention (via ORM)
- ✅ Authentication requirement enforcement
- ✅ Role-based access control validation
- ✅ Input validation and sanitization

Security scans are automatically run in CI/CD using Bandit and Safety tools.

## Performance Testing

While not included in the basic test suite, performance considerations:

- Tests use in-memory SQLite for speed
- Parallel execution available with `--parallel`
- Database queries optimized with proper joins
- Test fixtures reused where appropriate

## Maintenance

### Regular Maintenance Tasks

1. **Update Dependencies:** Keep test dependencies current
2. **Review Coverage:** Ensure coverage remains high
3. **Update Tests:** Add tests for new features
4. **Security Updates:** Keep security scanning tools updated

### Test Health Monitoring

Monitor test suite health:

- ✅ All tests passing in CI/CD
- ✅ Coverage above minimum threshold
- ✅ No security vulnerabilities detected
- ✅ Tests complete within reasonable time

The test suite is a critical component ensuring the platform's reliability and security. Regular execution and maintenance of these tests is essential for production readiness.
