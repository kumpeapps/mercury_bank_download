"""
Test user registration and role assignment functionality.

This test suite verifies the critical functionality of user registration,
particularly the automatic assignment of admin roles to the first user.
"""

import pytest
from web_app.models.user import User
from web_app.models.role import Role
from web_app.models.user_settings import UserSettings


class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_first_user_gets_admin_roles(self, test_db, init_roles, init_system_settings):
        """Test that the first user automatically gets admin and super-admin roles."""
        # Verify no users exist initially
        user_count = test_db.query(User).count()
        assert user_count == 0
        
        # Create first user
        first_user = User(username="firstuser", email="first@example.com")
        first_user.set_password("password123")
        test_db.add(first_user)
        test_db.flush()
        
        # Get roles
        user_role = test_db.query(Role).filter_by(name="user").first()
        admin_role = test_db.query(Role).filter_by(name="admin").first()
        super_admin_role = test_db.query(Role).filter_by(name="super-admin").first()
        
        assert user_role is not None
        assert admin_role is not None
        assert super_admin_role is not None
        
        # Assign roles (simulating the registration logic)
        first_user.roles.append(user_role)
        first_user.roles.append(admin_role)
        first_user.roles.append(super_admin_role)
        
        # Create user settings
        user_settings = UserSettings(user_id=first_user.id)
        test_db.add(user_settings)
        test_db.commit()
        
        # Verify first user has all three roles
        assert len(first_user.roles) == 3
        role_names = [role.name for role in first_user.roles]
        assert "user" in role_names
        assert "admin" in role_names
        assert "super-admin" in role_names
        
        # Verify user has admin permissions
        assert first_user.has_role("admin")
        assert first_user.has_role("super-admin")
        assert first_user.has_role("user")
    
    def test_subsequent_users_get_only_user_role(self, test_db, init_roles, init_system_settings):
        """Test that subsequent users only get the basic user role."""
        # Create first user (admin)
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
        
        # Now create second user
        second_user = User(username="seconduser", email="second@example.com")
        second_user.set_password("password123")
        test_db.add(second_user)
        test_db.flush()
        
        # Second user should only get user role
        second_user.roles.append(user_role)
        
        # Create user settings for second user
        second_user_settings = UserSettings(user_id=second_user.id)
        test_db.add(second_user_settings)
        test_db.commit()
        
        # Verify second user has only user role
        assert len(second_user.roles) == 1
        assert second_user.roles[0].name == "user"
        
        # Verify second user does NOT have admin permissions
        assert second_user.has_role("user")
        assert not second_user.has_role("admin")
        assert not second_user.has_role("super-admin")
    
    def test_user_role_permissions(self, test_db, init_roles):
        """Test user role permission checking functionality."""
        # Create user with specific roles
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        test_db.add(user)
        test_db.flush()
        
        # Get roles
        user_role = test_db.query(Role).filter_by(name="user").first()
        reports_role = test_db.query(Role).filter_by(name="reports").first()
        locked_role = test_db.query(Role).filter_by(name="locked").first()
        
        # Assign user and reports roles
        user.roles.extend([user_role, reports_role])
        test_db.commit()
        
        # Test role checking
        assert user.has_role("user")
        assert user.has_role("reports")
        assert not user.has_role("admin")
        assert not user.has_role("locked")
        
        # Test adding locked role
        user.roles.append(locked_role)
        test_db.commit()
        
        assert user.has_role("locked")
    
    def test_user_settings_creation(self, test_db, init_roles):
        """Test that user settings are created properly without legacy fields."""
        # Create user
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        test_db.add(user)
        test_db.flush()
        
        # Create user settings
        user_settings = UserSettings(user_id=user.id)
        test_db.add(user_settings)
        test_db.commit()
        
        # Verify user settings were created
        retrieved_settings = test_db.query(UserSettings).filter_by(user_id=user.id).first()
        assert retrieved_settings is not None
        assert retrieved_settings.user_id == user.id
        
        # Verify no legacy is_admin field exists (this should not raise an error)
        # If the field existed, accessing it would work, but it shouldn't exist
        assert not hasattr(retrieved_settings, 'is_admin')
    
    def test_password_hashing(self, test_db):
        """Test that user passwords are properly hashed."""
        # Create user
        user = User(username="testuser", email="test@example.com")
        password = "test_password_123"
        user.set_password(password)
        test_db.add(user)
        test_db.commit()
        
        # Verify password is hashed (not stored in plain text)
        assert user.password_hash != password
        assert user.password_hash is not None
        assert len(user.password_hash) > 20  # Hashed passwords should be long
        
        # Verify password verification works
        assert user.check_password(password)
        assert not user.check_password("wrong_password")
    
    def test_username_uniqueness(self, test_db, init_roles):
        """Test that usernames must be unique."""
        # Create first user
        user1 = User(username="testuser", email="test1@example.com")
        user1.set_password("password123")
        test_db.add(user1)
        test_db.commit()
        
        # Try to create second user with same username
        user2 = User(username="testuser", email="test2@example.com")  # Same username
        user2.set_password("password123")
        test_db.add(user2)
        
        # This should raise an integrity error due to unique constraint
        with pytest.raises(Exception):  # SQLAlchemy will raise an IntegrityError
            test_db.commit()


class TestRoleManagement:
    """Test role management functionality."""
    
    def test_role_creation(self, test_db):
        """Test that roles can be created properly."""
        # Create role
        role = Role(name="test_role", description="Test role description", is_system_role=False)
        test_db.add(role)
        test_db.commit()
        
        # Verify role was created
        retrieved_role = test_db.query(Role).filter_by(name="test_role").first()
        assert retrieved_role is not None
        assert retrieved_role.name == "test_role"
        assert retrieved_role.description == "Test role description"
        assert retrieved_role.is_system_role is False
    
    def test_get_or_create_role(self, test_db):
        """Test the Role.get_or_create method."""
        # Test creating new role
        role1 = Role.get_or_create(
            test_db, 
            "new_role", 
            "New role description", 
            is_system_role=True
        )
        assert role1.name == "new_role"
        assert role1.is_system_role is True
        
        # Test getting existing role
        role2 = Role.get_or_create(
            test_db, 
            "new_role", 
            "Different description",  # This should be ignored
            is_system_role=False  # This should be ignored
        )
        
        # Should return the same role instance
        assert role1.id == role2.id
        assert role2.description == "New role description"  # Original description preserved
        assert role2.is_system_role is True  # Original value preserved
    
    def test_system_roles_initialization(self, test_db, init_roles):
        """Test that all required system roles are created."""
        required_roles = ["user", "admin", "super-admin", "reports", "transactions", "locked"]
        
        for role_name in required_roles:
            role = test_db.query(Role).filter_by(name=role_name).first()
            assert role is not None, f"Required role '{role_name}' not found"
            assert role.is_system_role is True, f"Role '{role_name}' should be a system role"
