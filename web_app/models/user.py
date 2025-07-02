"""User model for managing user accounts and permissions."""

from sqlalchemy import Column, String, DateTime, Boolean, text, Integer
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import phpass
from .base import Base, user_mercury_account_association, user_account_access


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
        if not self.settings:
            return False
        return self.settings.is_admin

    def set_admin_status(self, is_admin, modifier_user=None):
        """
        Set the admin status for this user. Only admins can modify admin status.
        
        Args:
            is_admin (bool): Whether the user should have admin privileges
            modifier_user (User, optional): The user making the change (must be admin)
            
        Returns:
            bool: True if the change was successful, False if not authorized
        """
        # Only admins can modify admin status
        if modifier_user and not modifier_user.is_admin:
            return False
            
        # Ensure user has settings
        if not self.settings:
            from .user_settings import UserSettings
            self.settings = UserSettings(user_id=self.id)
            
        self.settings.is_admin = is_admin
        return True

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
        accessible_accounts = []
        for mercury_account in self.mercury_accounts:
            accounts = db_session.query(Account).filter_by(mercury_account_id=mercury_account.id).all()
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
