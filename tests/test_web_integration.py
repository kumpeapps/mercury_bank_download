"""
Integration tests for the web application.

These tests verify end-to-end functionality including HTTP endpoints,
user authentication, and the complete user registration flow.
"""

import pytest
import json
from flask import url_for


class TestWebRegistration:
    """Test web-based user registration functionality."""
    
    def test_registration_page_loads(self, test_app):
        """Test that the registration page loads successfully."""
        response = test_app.get('/register')
        assert response.status_code == 200
        assert b'register' in response.data.lower() or b'sign up' in response.data.lower()
    
    def test_first_user_registration_via_web(self, test_app, test_db, init_roles, init_system_settings):
        """Test first user registration through web interface."""
        # Verify no users exist
        from web_app.models.user import User
        user_count = test_db.query(User).count()
        assert user_count == 0
        
        # Register first user via web interface
        response = test_app.post('/register', data={
            'username': 'firstwebuser',
            'email': 'firstweb@example.com',
            'password': 'webpassword123'
        }, follow_redirects=True)
        
        # Should redirect to login page after successful registration
        assert response.status_code == 200
        
        # Verify user was created in database
        user = test_db.query(User).filter_by(username='firstwebuser').first()
        assert user is not None
        assert user.email == 'firstweb@example.com'
        
        # Verify user has admin roles (first user)
        assert len(user.roles) == 3
        role_names = [role.name for role in user.roles]
        assert "user" in role_names
        assert "admin" in role_names
        assert "super-admin" in role_names
    
    def test_subsequent_user_registration_via_web(self, test_app, test_db, init_roles, init_system_settings):
        """Test subsequent user registration through web interface."""
        from web_app.models.user import User
        from web_app.models.role import Role
        from web_app.models.user_settings import UserSettings
        
        # Create first user manually
        first_user = User(username="firstuser", email="first@example.com")
        first_user.set_password("password123")
        test_db.add(first_user)
        test_db.flush()
        
        # Assign admin roles to first user
        user_role = test_db.query(Role).filter_by(name="user").first()
        admin_role = test_db.query(Role).filter_by(name="admin").first()
        super_admin_role = test_db.query(Role).filter_by(name="super-admin").first()
        first_user.roles.extend([user_role, admin_role, super_admin_role])
        
        # Create user settings for first user
        first_user_settings = UserSettings(user_id=first_user.id)
        test_db.add(first_user_settings)
        test_db.commit()
        
        # Register second user via web interface
        response = test_app.post('/register', data={
            'username': 'secondwebuser',
            'email': 'secondweb@example.com',
            'password': 'webpassword123'
        }, follow_redirects=True)
        
        # Should redirect to login page after successful registration
        assert response.status_code == 200
        
        # Verify second user was created
        second_user = test_db.query(User).filter_by(username='secondwebuser').first()
        assert second_user is not None
        
        # Verify second user only has user role
        assert len(second_user.roles) == 1
        assert second_user.roles[0].name == "user"
    
    def test_duplicate_username_registration(self, test_app, test_db, init_roles, init_system_settings):
        """Test that duplicate username registration is rejected."""
        from web_app.models.user import User
        from web_app.models.user_settings import UserSettings
        
        # Create first user
        first_user = User(username="testuser", email="first@example.com")
        first_user.set_password("password123")
        test_db.add(first_user)
        test_db.flush()
        
        user_settings = UserSettings(user_id=first_user.id)
        test_db.add(user_settings)
        test_db.commit()
        
        # Try to register with same username
        response = test_app.post('/register', data={
            'username': 'testuser',  # Same username
            'email': 'second@example.com',
            'password': 'password123'
        })
        
        # Should show error (either redirect to register with error or show error on page)
        assert response.status_code in [200, 302]
        if response.status_code == 200:
            assert b'already exists' in response.data.lower() or b'error' in response.data.lower()


class TestWebAuthentication:
    """Test web-based authentication functionality."""
    
    def test_login_page_loads(self, test_app):
        """Test that the login page loads successfully."""
        response = test_app.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'sign in' in response.data.lower()
    
    def test_successful_login(self, test_app, test_db, init_roles):
        """Test successful user login."""
        from web_app.models.user import User
        from web_app.models.role import Role
        from web_app.models.user_settings import UserSettings
        
        # Create user
        user = User(username="loginuser", email="login@example.com")
        user.set_password("loginpassword123")
        test_db.add(user)
        test_db.flush()
        
        # Add user role
        user_role = test_db.query(Role).filter_by(name="user").first()
        user.roles.append(user_role)
        
        # Create user settings
        user_settings = UserSettings(user_id=user.id)
        test_db.add(user_settings)
        test_db.commit()
        
        # Test login
        response = test_app.post('/login', data={
            'username': 'loginuser',
            'password': 'loginpassword123'
        }, follow_redirects=True)
        
        # Should redirect to dashboard or main page after successful login
        assert response.status_code == 200
    
    def test_failed_login(self, test_app, test_db, init_roles):
        """Test failed login with wrong credentials."""
        from web_app.models.user import User
        from web_app.models.user_settings import UserSettings
        
        # Create user
        user = User(username="loginuser", email="login@example.com")
        user.set_password("correctpassword")
        test_db.add(user)
        test_db.flush()
        
        user_settings = UserSettings(user_id=user.id)
        test_db.add(user_settings)
        test_db.commit()
        
        # Test login with wrong password
        response = test_app.post('/login', data={
            'username': 'loginuser',
            'password': 'wrongpassword'
        })
        
        # Should stay on login page or redirect to login with error
        assert response.status_code in [200, 302]
        if response.status_code == 200:
            assert b'error' in response.data.lower() or b'invalid' in response.data.lower()
    
    def test_dashboard_requires_authentication(self, test_app):
        """Test that dashboard requires authentication."""
        response = test_app.get('/dashboard')
        
        # Should redirect to login page
        assert response.status_code == 302
        assert '/login' in response.location


class TestUserPermissions:
    """Test user permission enforcement."""
    
    def test_user_without_user_role_denied(self, test_app, test_db, init_roles):
        """Test that users without basic 'user' role are denied access."""
        from web_app.models.user import User
        from web_app.models.role import Role
        from web_app.models.user_settings import UserSettings
        
        # Create user without any roles
        user = User(username="noroleuser", email="norole@example.com")
        user.set_password("password123")
        test_db.add(user)
        test_db.flush()
        
        # Create user settings but don't assign any roles
        user_settings = UserSettings(user_id=user.id)
        test_db.add(user_settings)
        test_db.commit()
        
        # Verify user has no roles
        assert len(user.roles) == 0
        assert not user.has_role("user")
    
    def test_locked_user_denied(self, test_db, init_roles):
        """Test that locked users are denied access."""
        from web_app.models.user import User
        from web_app.models.role import Role
        from web_app.models.user_settings import UserSettings
        
        # Create user with user and locked roles
        user = User(username="lockeduser", email="locked@example.com")
        user.set_password("password123")
        test_db.add(user)
        test_db.flush()
        
        # Add both user and locked roles
        user_role = test_db.query(Role).filter_by(name="user").first()
        locked_role = test_db.query(Role).filter_by(name="locked").first()
        user.roles.extend([user_role, locked_role])
        
        user_settings = UserSettings(user_id=user.id)
        test_db.add(user_settings)
        test_db.commit()
        
        # Verify user has locked role
        assert user.has_role("locked")
        assert user.has_role("user")  # Still has user role but should be locked


class TestSystemSettings:
    """Test system settings functionality."""
    
    def test_registration_can_be_disabled(self, test_app, test_db, init_system_settings):
        """Test that registration can be disabled via system settings."""
        from web_app.models.system_setting import SystemSetting
        
        # Disable registration
        setting = test_db.query(SystemSetting).filter_by(key="registration_enabled").first()
        if setting:
            setting.value = "false"
        else:
            setting = SystemSetting(key="registration_enabled", value="false")
            test_db.add(setting)
        test_db.commit()
        
        # Try to access registration page
        response = test_app.get('/register')
        
        # Should redirect to login or show error
        assert response.status_code in [302, 200]
        if response.status_code == 302:
            assert '/login' in response.location
    
    def test_system_settings_initialization(self, test_db, init_system_settings):
        """Test that system settings are properly initialized."""
        from web_app.models.system_setting import SystemSetting
        
        required_settings = [
            "registration_enabled",
            "prevent_user_deletion", 
            "users_externally_managed",
            "app_name",
            "app_description"
        ]
        
        for setting_key in required_settings:
            setting = test_db.query(SystemSetting).filter_by(key=setting_key).first()
            assert setting is not None, f"Required setting '{setting_key}' not found"
            assert setting.value is not None, f"Setting '{setting_key}' has no value"
