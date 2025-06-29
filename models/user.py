"""User model for managing user accounts and permissions."""

from sqlalchemy import Column, String, DateTime, Boolean, text, Table, ForeignKey, Integer
from sqlalchemy.orm import relationship
from .base import Base

# Association table for many-to-many relationship between users and mercury accounts
user_mercury_account_association = Table(
    "user_mercury_accounts",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "mercury_account_id",
        Integer,
        ForeignKey("mercury_accounts.id"),
        primary_key=True,
    ),
)


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
        is_admin (bool): Whether the user has admin privileges, defaults to False
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
    is_admin = Column(Boolean, default=False)

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
