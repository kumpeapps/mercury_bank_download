"""
Test configuration for Mercury Bank Integration Platform tests.
"""

import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure required environment variables are set for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-not-for-production")
os.environ.setdefault("USERS_EXTERNALLY_MANAGED", "false")

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
def test_app(test_db):
    """Provide a test Flask application."""
    import sys
    import os
    
    # Add web_app to Python path
    web_app_path = os.path.join(os.path.dirname(__file__), '..', 'web_app')
    sys.path.insert(0, web_app_path)
    
    # Set environment variables for test app
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["USERS_EXTERNALLY_MANAGED"] = "false"
    
    # Import Flask and create a new app instance
    from flask import Flask
    from flask_login import LoginManager
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create test app
    test_flask_app = Flask(__name__, 
                          template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                          static_folder=os.path.join(web_app_path, 'static'))
    
    # Configure test app
    test_flask_app.config.update({
        'SECRET_KEY': 'test-secret-key-for-testing-only',
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'DATABASE_URL': TEST_DATABASE_URL
    })
    
    # Create test database engine and session
    test_engine = create_engine(TEST_DATABASE_URL, echo=False)
    TestSession = sessionmaker(bind=test_engine)
    
    # Import models to register them
    from web_app.models.base import Base
    from web_app.models.user import User
    from web_app.models.user_settings import UserSettings
    from web_app.models.role import Role
    from web_app.models.system_setting import SystemSetting
    from web_app.models.mercury_account import MercuryAccount
    from web_app.models.account import Account
    from web_app.models.transaction import Transaction
    from web_app.models.transaction_attachment import TransactionAttachment
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(test_flask_app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        db_session = test_db
        try:
            return db_session.query(User).get(int(user_id))
        except:
            return None
    
    # Register routes with test session
    register_test_routes(test_flask_app, test_db)
    
    with test_flask_app.test_client() as client:
        with test_flask_app.app_context():
            yield client


def register_test_routes(app, test_session):
    """Register test routes that use the test database session."""
    from flask import render_template, request, redirect, url_for, flash
    from flask_login import login_user, current_user
    from werkzeug.security import generate_password_hash
    from web_app.models.user import User
    from web_app.models.user_settings import UserSettings
    from web_app.models.role import Role
    from web_app.models.system_setting import SystemSetting
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Handle user registration."""
        if request.method == 'GET':
            return render_template('register.html')
        
        # Handle POST request
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('register'))
        
        try:
            # Check if user already exists
            existing_user = test_session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                flash('Username or email already exists', 'error')
                return redirect(url_for('register'))
            
            # Create new user
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            test_session.add(new_user)
            test_session.flush()  # Get the user ID
            
            # Create user settings
            user_settings = UserSettings(user_id=new_user.id)
            test_session.add(user_settings)
            
            # Assign roles
            user_count = test_session.query(User).count()
            
            # Always assign user role
            user_role = test_session.query(Role).filter_by(name="user").first()
            if user_role:
                new_user.roles.append(user_role)
            
            # If first user, assign admin roles
            if user_count == 1:
                admin_role = test_session.query(Role).filter_by(name="admin").first()
                super_admin_role = test_session.query(Role).filter_by(name="super-admin").first()
                
                if admin_role:
                    new_user.roles.append(admin_role)
                if super_admin_role:
                    new_user.roles.append(super_admin_role)
            
            test_session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            test_session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('register'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Handle user login."""
        if request.method == 'GET':
            return render_template('login.html')
        
        # Handle POST request
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        try:
            user = test_session.query(User).filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
                return render_template('login.html')
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
            return render_template('login.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard route that requires authentication."""
        from flask_login import login_required
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return f"Welcome to dashboard, {current_user.username}!"

    @app.route('/admin/users')
    def admin_users():
        """Admin users management page."""
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if not (hasattr(current_user, 'has_role') and 
                (current_user.has_role('admin') or current_user.has_role('super-admin'))):
            return redirect(url_for('dashboard'))
        
        return "Admin Users Page"

    @app.route('/admin/users/<int:user_id>/settings', methods=['GET', 'POST'])
    def edit_user_settings(user_id):
        """Edit user settings - super-admin only."""
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if not (hasattr(current_user, 'has_role') and current_user.has_role('super-admin')):
            return redirect(url_for('dashboard'))
        
        # Get the user to edit
        user = test_session.query(User).get(user_id)
        if not user:
            return "User not found", 404
        
        if request.method == 'GET':
            return f"Edit User Settings for {user.username}"
        
        # Handle POST request (settings update)
        return redirect(url_for('admin_users'))


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
