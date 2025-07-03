"""System settings model for managing application configuration."""

from sqlalchemy import Column, String, Text, Boolean, DateTime, text
from .base import Base


class SystemSetting(Base):
    """
    SQLAlchemy model for storing system-wide configuration settings.

    This model stores key-value pairs for application settings such as
    whether user registration is enabled, email configuration, etc.

    Attributes:
        key (str): Primary key - unique setting identifier
        value (str): Setting value (stored as text to support various data types)
        description (str, optional): Human-readable description of the setting
        is_editable (bool): Whether this setting can be modified through the UI
        created_at (datetime): Timestamp when setting was created
        updated_at (datetime): Timestamp when setting was last modified
    """

    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_editable = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self):
        return f"<SystemSetting(key='{self.key}', value='{self.value}')>"

    @classmethod
    def get_value(cls, session, key, default=None):
        """
        Get a setting value by key.

        Args:
            session: Database session
            key (str): Setting key
            default: Default value if setting doesn't exist

        Returns:
            Setting value or default
        """
        setting = session.query(cls).filter_by(key=key).first()
        return setting.value if setting else default

    @classmethod
    def set_value(cls, session, key, value, description=None, is_editable=True):
        """
        Set a setting value by key.

        Args:
            session: Database session
            key (str): Setting key
            value (str): Setting value
            description (str, optional): Setting description
            is_editable (bool): Whether setting can be edited via UI
        """
        setting = session.query(cls).filter_by(key=key).first()
        if setting:
            setting.value = str(value)
            if description:
                setting.description = description
            setting.is_editable = is_editable
        else:
            setting = cls(
                key=key,
                value=str(value),
                description=description,
                is_editable=is_editable,
            )
            session.add(setting)
        session.commit()

    @classmethod
    def get_bool_value(cls, session, key, default=False):
        """
        Get a boolean setting value.

        Args:
            session: Database session
            key (str): Setting key
            default (bool): Default value if setting doesn't exist

        Returns:
            bool: Setting value as boolean
        """
        value = cls.get_value(session, key, str(default))
        return str(value).lower() in ("true", "1", "yes", "on")
