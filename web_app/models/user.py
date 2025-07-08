"""User model for managing user accounts and permissions."""

from sqlalchemy import Column, String, DateTime, Boolean, text, Integer
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import phpass # type: ignore
from .base import Base, user_mercury_account_association, user_account_access
from .role import user_role_association


class User(Base):
    """
    SQLAlchemy model representing a user in the system.

    This model stores user authentication and profile information. Users can be granted
    access to one or more Mercury account groups through the many-to-many relationship
    with MercuryAccount. This allows for flexible permission management where multiple
    users can access the same Mercury account group, and users can access multiple
    account groups.

    Attributes:
        id (str): Primary key - unique user identifier
        username (str): Unique username for login
        email (str): User's email address (unique)
        password_hash (str): Hashed password for authentication
        first_name (str, optional): User's first name
        last_name (str, optional): User's last name
        is_active (bool): Whether the user account is active, defaults to True
        last_login (datetime, optional): Timestamp of last successful login
        created_at (datetime): Timestamp when user was created
        updated_at (datetime): Timestamp when user was last updated

        mercury_accounts (list): List of MercuryAccount objects this user has access to
    """

    __tablename__ = "users"

    # Core user fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # Status and permissions
    is_active = Column(Boolean, default=True)

    # Timestamps
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Many-to-many relationship with MercuryAccount
    mercury_accounts = relationship(
        "MercuryAccount",
        secondary=user_mercury_account_association,
        back_populates="users",
    )

    # Many-to-many relationship with Roles
    roles = relationship(
        "Role",
        secondary=user_role_association,
        back_populates="users",
    )

    # Many-to-many relationship with Account for granular access control
    # When this relationship has entries, it restricts user access to only those specific accounts
    # If empty, user has access to all accounts in their mercury_accounts (default behavior)
    # Explicit join conditions since user_id doesn't have a foreign key constraint
    restricted_accounts = relationship(
        "Account",
        secondary=user_account_access,
        primaryjoin="User.id == user_account_access.c.user_id",
        secondaryjoin="Account.id == user_account_access.c.account_id",
        back_populates="authorized_users",
    )

    # One-to-one relationship with UserSettings
    settings = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        """
        Return a string representation of the User instance.

        Returns:
            str: A formatted string showing the username and email
        """
        return f"<User(username='{self.username}', email='{self.email}')>"

    @property
    def full_name(self):
        """
        Get the user's full name.

        Returns:
            str: Combined first and last name, or just the available name parts
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    @property
    def is_admin(self):
        """
        Check if the user has admin privileges.
        
        Returns:
            bool: True if user has admin privileges, False otherwise
        """
        return self.has_role('admin') or self.has_role("super-admin")
        
    @property
    def is_super_admin(self):
        """
        Check if the user has super admin privileges.
        
        Returns:
            bool: True if user has super admin privileges, False otherwise
        """
        return self.has_role('super-admin')
        
    def has_role(self, role_name):
        """
        Check if the user has a specific role.
        
        Args:
            role_name (str): The name of the role to check for
            
        Returns:
            bool: True if user has the role, False otherwise
        """
        return any(role.name == role_name for role in self.roles)
        
    def has_any_role(self, role_names):
        """
        Check if the user has any of the specified roles.
        
        Args:
            role_names (list): A list of role names to check for
            
        Returns:
            bool: True if user has any of the roles, False otherwise
        """
        if not role_names:
            return False
        return any(self.has_role(role_name) for role_name in role_names)
        
    def has_all_roles(self, role_names):
        """
        Check if the user has all of the specified roles.
        
        Args:
            role_names (list): A list of role names to check for
            
        Returns:
            bool: True if user has all of the roles, False otherwise
        """
        if not role_names:
            return True
        return all(self.has_role(role_name) for role_name in role_names)
        
    def add_role(self, role, db_session):
        """
        Add a role to the user.
        
        Args:
            role: The Role object or role name to add
            db_session: SQLAlchemy session
            
        Returns:
            bool: True if role was added, False if already exists or error
        """
        # If role is a string, get or create the role object
        if isinstance(role, str):
            from .role import Role
            role = Role.get_or_create(db_session, role)
            
        # Check if user already has this role
        if role in self.roles:
            return False
            
        self.roles.append(role)
        return True
        
    def remove_role(self, role, db_session):
        """
        Remove a role from the user.
        
        Args:
            role: The Role object or role name to remove
            db_session: SQLAlchemy session
            
        Returns:
            bool: True if role was removed, False if not found or error
        """
        # If role is a string, find the role object
        if isinstance(role, str):
            from .role import Role
            role_obj = db_session.query(Role).filter_by(name=role).first()
            if not role_obj:
                return False
            role = role_obj
            
        # Check if user has this role
        if role not in self.roles:
            return False
            
        self.roles.remove(role)
        return True
        
    def can_access_transactions(self):
        """
        Check if user has permission to access the transactions page.
        
        Returns:
            bool: True if user can access transactions, False otherwise
        """
        # Super admins and admins always have access
        if self.is_super_admin or self.is_admin:
            return True
            
        # Users with the 'transactions' role have access
        return self.has_role('transactions')
        
    def can_access_reports(self):
        """
        Check if user has permission to access the reports page.
        
        Returns:
            bool: True if user can access reports, False otherwise
        """
        # Super admins and admins always have access
        if self.is_super_admin or self.is_admin:
            return True
            
        # Users with the 'reports' role have access
        return self.has_role('reports')
        
    def can_manage_system_settings(self):
        """
        Check if user has permission to manage system settings.
        
        Returns:
            bool: True if user can manage system settings, False otherwise
        """
        # Only super admins can manage system settings
        return self.is_super_admin
        
    def can_manage_users(self):
        """
        Check if user has permission to manage users.
        
        Returns:
            bool: True if user can manage users, False otherwise
        """
        # Only super admins can manage users
        return self.is_super_admin
        
    def can_manage_mercury_accounts(self):
        """
        Check if user has permission to manage Mercury accounts.
        
        Returns:
            bool: True if user can manage Mercury accounts, False otherwise
        """
        # Super admins and admins can manage Mercury accounts
        return self.is_super_admin or self.is_admin
        
    def can_manage_account_settings(self):
        """
        Check if user has permission to manage account settings.
        
        Returns:
            bool: True if user can manage account settings, False otherwise
        """
        # Super admins and admins can manage account settings
        return self.is_super_admin or self.is_admin

    # Flask-Login methods
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True

    def is_anonymous(self):
        """Return False as this is an authenticated user."""
        return False

    def get_id(self):
        """Return the user ID as a string (required by Flask-Login)."""
        return str(self.id)

    def set_password(self, password):
        """
        Set the user's password by hashing it.

        Args:
            password (str): The plain text password to hash and store
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Check if the provided password matches the user's stored password hash.
        Supports both PHPass (legacy) and Werkzeug (new) hash formats.

        Args:
            password (str): The plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        if not self.password_hash or not self.password_hash.strip():
            return False

        hash_value = self.password_hash.strip()

        # Check if it's a PHPass hash (starts with $P$ or $H$)
        if hash_value.startswith(("$P$", "$H$")):
            try:
                return phpass.verify(password, hash_value)
            except (ValueError, TypeError):
                return False

        # Check if it's a Werkzeug hash (contains method prefix like pbkdf2:sha256:)
        elif ":" in hash_value and any(
            method in hash_value for method in ["pbkdf2", "scrypt", "argon2"]
        ):
            try:
                return check_password_hash(hash_value, password)
            except ValueError:
                return False

        # For other formats, try both
        try:
            # Try PHPass first (more likely for legacy data)
            if phpass.verify(password, hash_value):
                return True
        except (ValueError, TypeError):
            pass

        try:
            # Try Werkzeug format
            return check_password_hash(hash_value, password)
        except ValueError:
            return False

    def has_valid_password(self):
        """
        Check if the user has a valid password hash.
        Supports both PHPass and Werkzeug formats.

        Returns:
            bool: True if password hash is valid, False otherwise
        """
        if not self.password_hash or not self.password_hash.strip():
            return False

        hash_value = self.password_hash.strip()

        # Check if it's a PHPass hash (starts with $P$ or $H$)
        if hash_value.startswith(("$P$", "$H$")):
            return (
                True  # PHPass hashes are generally valid if they have the right prefix
            )

        # Check if it's a Werkzeug hash (contains method prefix)
        if ":" in hash_value and any(
            method in hash_value for method in ["pbkdf2", "scrypt", "argon2"]
        ):
            try:
                # Try to validate the hash format by checking against a dummy password
                check_password_hash(hash_value, "dummy_password")
                return True
            except ValueError:
                return False

        # For other formats, assume they might be valid (legacy hashes)
        return len(hash_value) > 10  # Basic length check

    def get_accessible_accounts(self, db_session):
        """
        Get all accounts this user has access to.
        
        If the user has specific account restrictions (entries in restricted_accounts),
        return only those accounts. Otherwise, return all accounts from their mercury_accounts.
        
        Args:
            db_session: SQLAlchemy session to use for queries
            
        Returns:
            list: List of Account objects the user can access
        """
        # If user has specific account restrictions, return only those
        if self.restricted_accounts:
            return self.restricted_accounts
        
        # Otherwise, return all accounts from all mercury accounts the user has access to
        from .account import Account
        from sqlalchemy.orm import joinedload
        accessible_accounts = []
        for mercury_account in self.mercury_accounts:
            accounts = db_session.query(Account).options(
                joinedload(Account.mercury_account)  # Eagerly load mercury_account relationship
            ).filter_by(mercury_account_id=mercury_account.id).all()
            accessible_accounts.extend(accounts)
        
        return accessible_accounts
    
    def has_account_access(self, account_id, db_session):
        """
        Check if the user has access to a specific account.
        
        Args:
            account_id: The ID of the account to check
            db_session: SQLAlchemy session to use for queries
            
        Returns:
            bool: True if user has access, False otherwise
        """
        accessible_accounts = self.get_accessible_accounts(db_session)
        return any(account.id == account_id for account in accessible_accounts)
