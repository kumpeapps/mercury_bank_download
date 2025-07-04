"""
Test configuration for Mercury Bank Integration Platform tests.
"""

import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database configuration
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", 
    "sqlite:///:memory:"  # Default to in-memory SQLite for tests
)

class TestConfig:
    """Test configuration settings."""
    
    # Database settings
    DATABASE_URL = TEST_DATABASE_URL
    
    # Security settings
    SECRET_KEY = "test-secret-key-for-testing-only"
    
    # Environment settings
    USERS_EXTERNALLY_MANAGED = False
    SYNC_DAYS_BACK = 5
    SYNC_INTERVAL_MINUTES = 1
    RUN_ONCE = True
    
    # Flask settings
    TESTING = True
    WTF_CSRF_ENABLED = False
    
    @staticmethod
    def get_test_engine():
        """Create a test database engine."""
        return create_engine(TEST_DATABASE_URL, echo=False)
    
    @staticmethod
    def get_test_session():
        """Create a test database session."""
        engine = TestConfig.get_test_engine()
        Session = sessionmaker(bind=engine)
        return Session()


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return TestConfig


@pytest.fixture(scope="function")
def test_db():
    """Provide a clean test database for each test."""
    engine = TestConfig.get_test_engine()
    
    # Import all models to ensure they are registered
    from web_app.models.base import Base
    from web_app.models.user import User
    from web_app.models.user_settings import UserSettings
    from web_app.models.role import Role
    from web_app.models.system_setting import SystemSetting
    from web_app.models.mercury_account import MercuryAccount
    from web_app.models.account import Account
    from web_app.models.transaction import Transaction
    from web_app.models.transaction_attachment import TransactionAttachment
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Cleanup
    session.close()
    if TEST_DATABASE_URL == "sqlite:///:memory:":
        # For in-memory SQLite, just drop all tables
        Base.metadata.drop_all(engine)
    else:
        # For other databases, truncate tables
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture(scope="function")
def test_app():
    """Provide a test Flask application."""
    import sys
    import os
    
    # Add web_app to Python path
    web_app_path = os.path.join(os.path.dirname(__file__), '..', 'web_app')
    sys.path.insert(0, web_app_path)
    
    from web_app.app import app
    
    # Configure app for testing
    app.config.update(TestConfig.__dict__)
    app.testing = True
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope="function")
def init_roles(test_db):
    """Initialize standard system roles."""
    from web_app.models.role import Role
    
    roles = [
        Role(name="user", description="Basic user with read access to their own data", is_system_role=True),
        Role(name="admin", description="Administrator with full system access", is_system_role=True),
        Role(name="super-admin", description="Super administrator with all privileges including user management", is_system_role=True),
        Role(name="reports", description="Access to all reports and analytics", is_system_role=True),
        Role(name="transactions", description="Full access to transaction data", is_system_role=True),
        Role(name="locked", description="Locked user account", is_system_role=True),
    ]
    
    for role in roles:
        test_db.add(role)
    
    test_db.commit()
    return roles


@pytest.fixture(scope="function")
def init_system_settings(test_db):
    """Initialize system settings."""
    from web_app.models.system_setting import SystemSetting
    
    settings = [
        SystemSetting(key="registration_enabled", value="true"),
        SystemSetting(key="prevent_user_deletion", value="false"),
        SystemSetting(key="users_externally_managed", value="false"),
        SystemSetting(key="app_name", value="Mercury Bank Integration"),
        SystemSetting(key="app_description", value="Mercury Bank data synchronization and management platform"),
        SystemSetting(key="logo_url", value=""),
    ]
    
    for setting in settings:
        test_db.add(setting)
    
    test_db.commit()
    return settings
