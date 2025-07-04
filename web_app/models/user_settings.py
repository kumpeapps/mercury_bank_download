"""User settings model for storing user preferences and configuration."""

from sqlalchemy import Column, DateTime, Boolean, text, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship, object_session
from .base import Base


class UserSettings(Base):
    """
    SQLAlchemy model representing user settings and preferences.

    This model stores user-specific settings and preferences that can be customized
    without affecting the core User model. Settings are stored in a flexible format
    to allow for easy extension.

    Attributes:
        id (int): Primary key - unique identifier
        user_id (int): Foreign key reference to the User
        primary_mercury_account_id (int, optional): Default Mercury account for filtering
        primary_account_id (int, optional): Default account within Mercury account for filtering
        dashboard_preferences (dict, optional): JSON object storing dashboard preferences
        report_preferences (dict, optional): JSON object storing report preferences
        created_at (datetime): Timestamp when settings were created
        updated_at (datetime): Timestamp when settings were last updated

        user (User): User object this settings belongs to
        primary_mercury_account (MercuryAccount): Primary Mercury account object
        primary_account (Account): Primary account object
    """

    __tablename__ = "user_settings"

    # Core identification fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)

    # Primary Mercury account for default filtering
    primary_mercury_account_id = Column(Integer, ForeignKey('mercury_accounts.id'), nullable=True)
    
    # Primary account within the Mercury account for default filtering
    primary_account_id = Column(String(255), ForeignKey('accounts.id'), nullable=True)

    # JSON fields for flexible settings storage
    dashboard_preferences = Column(JSON, nullable=True, default=lambda: {})
    report_preferences = Column(JSON, nullable=True, default=lambda: {})
    transaction_preferences = Column(JSON, nullable=True, default=lambda: {})

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    user = relationship("User", back_populates="settings")
    primary_mercury_account = relationship(
        "MercuryAccount",
        foreign_keys=[primary_mercury_account_id]
    )
    primary_account = relationship(
        "Account",
        foreign_keys=[primary_account_id]
    )

    def __repr__(self):
        """
        Return a string representation of the UserSettings instance.

        Returns:
            str: A formatted string showing the user_id and primary account
        """
        return f"<UserSettings(user_id={self.user_id}, primary_mercury_account_id={self.primary_mercury_account_id})>"

    def get_dashboard_preference(self, key, default=None):
        """
        Get a specific dashboard preference value.

        Args:
            key (str): The preference key to retrieve
            default: Default value to return if key doesn't exist

        Returns:
            The preference value or default
        """
        if not self.dashboard_preferences:
            return default
        return self.dashboard_preferences.get(key, default)

    def set_dashboard_preference(self, key, value):
        """
        Set a specific dashboard preference value.

        Args:
            key (str): The preference key to set
            value: The value to set
        """
        if not self.dashboard_preferences:
            self.dashboard_preferences = {}
        self.dashboard_preferences[key] = value

    def get_report_preference(self, key, default=None):
        """
        Get a specific report preference value.

        Args:
            key (str): The preference key to retrieve
            default: Default value to return if key doesn't exist

        Returns:
            The preference value or default
        """
        if not self.report_preferences:
            return default
        return self.report_preferences.get(key, default)

    def set_report_preference(self, key, value):
        """
        Set a specific report preference value.

        Args:
            key (str): The preference key to set
            value: The value to set
        """
        if not self.report_preferences:
            self.report_preferences = {}
        self.report_preferences[key] = value

    def get_transaction_preference(self, key, default=None):
        """
        Get a specific transaction preference value.

        Args:
            key (str): The preference key to retrieve
            default: Default value to return if key doesn't exist

        Returns:
            The preference value or default
        """
        if not self.transaction_preferences:
            return default
        return self.transaction_preferences.get(key, default)

    def set_transaction_preference(self, key, value):
        """
        Set a specific transaction preference value.

        Args:
            key (str): The preference key to set
            value: The value to set
        """
        if not self.transaction_preferences:
            self.transaction_preferences = {}
        self.transaction_preferences[key] = value
