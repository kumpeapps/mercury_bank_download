"""User settings model for storing user preferences and configuration."""

from sqlalchemy import (
    Column,
    DateTime,
    Boolean,
    text,
    Integer,
    String,
    ForeignKey,
    JSON,
)
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Primary Mercury account for default filtering
    primary_mercury_account_id = Column(
        Integer, ForeignKey("mercury_accounts.id"), nullable=True
    )

    # Primary account within the Mercury account for default filtering
    primary_account_id = Column(String(255), ForeignKey("accounts.id"), nullable=True)

    # JSON fields for flexible settings storage
    dashboard_preferences = Column(JSON, nullable=True, default=lambda: {})
    report_preferences = Column(JSON, nullable=True, default=lambda: {})
    transaction_preferences = Column(JSON, nullable=True, default=lambda: {})

    # Notification preferences
    email_notifications_enabled = Column(Boolean, default=True, nullable=False)
    pushover_notifications_enabled = Column(Boolean, default=False, nullable=False)
    pushover_user_key = Column(String(255), nullable=True)
    approval_email_notifications = Column(Boolean, default=True, nullable=False)
    approval_pushover_notifications = Column(Boolean, default=False, nullable=False)

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
        "MercuryAccount", foreign_keys=[primary_mercury_account_id]
    )
    primary_account = relationship("Account", foreign_keys=[primary_account_id])

    def __repr__(self):
        """
        Return a string representation of the UserSettings instance.

        Returns:
            str: A formatted string showing the user_id and primary account
        """
        return f"<UserSettings(user_id={self.user_id}, primary_mercury_account_id={self.primary_mercury_account_id})>"

    def _ensure_dict(self, value):
        """
        Ensure a value is a dictionary, parsing from JSON string if necessary.
        
        Args:
            value: The value to ensure is a dict
            
        Returns:
            dict: The value as a dictionary, or empty dict if conversion fails
        """
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return {}
        return {}

    def get_dashboard_preference(self, key, default=None):
        """
        Get a specific dashboard preference value.

        Args:
            key (str): The preference key to retrieve
            default: Default value to return if key doesn't exist

        Returns:
            The preference value or default
        """
        preferences = self._ensure_dict(self.dashboard_preferences)
        if not preferences:
            return default
        return preferences.get(key, default)

    def set_dashboard_preference(self, key, value):
        """
        Set a specific dashboard preference value.

        Args:
            key (str): The preference key to set
            value: The value to set
        """
        preferences = self._ensure_dict(self.dashboard_preferences)
        if not preferences:
            preferences = {}
        preferences[key] = value
        self.dashboard_preferences = preferences

    def get_report_preference(self, key, default=None):
        """
        Get a specific report preference value.

        Args:
            key (str): The preference key to retrieve
            default: Default value to return if key doesn't exist

        Returns:
            The preference value or default
        """
        preferences = self._ensure_dict(self.report_preferences)
        if not preferences:
            return default
        return preferences.get(key, default)

    def set_report_preference(self, key, value):
        """
        Set a specific report preference value.

        Args:
            key (str): The preference key to set
            value: The value to set
        """
        preferences = self._ensure_dict(self.report_preferences)
        if not preferences:
            preferences = {}
        preferences[key] = value
        self.report_preferences = preferences

    def get_transaction_preference(self, key, default=None):
        """
        Get a specific transaction preference value.

        Args:
            key (str): The preference key to retrieve
            default: Default value to return if key doesn't exist

        Returns:
            The preference value or default
        """
        preferences = self._ensure_dict(self.transaction_preferences)
        if not preferences:
            return default
        return preferences.get(key, default)

    def set_transaction_preference(self, key, value):
        """
        Set a specific transaction preference value.

        Args:
            key (str): The preference key to set
            value: The value to set
        """
        preferences = self._ensure_dict(self.transaction_preferences)
        if not preferences:
            preferences = {}
        preferences[key] = value
        self.transaction_preferences = preferences
