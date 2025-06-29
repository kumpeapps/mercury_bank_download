from sqlalchemy import Column, String, DateTime, Boolean, Text, text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from .user import user_mercury_account_association


class MercuryAccount(Base):
    """
    SQLAlchemy model representing a Mercury Bank account group configuration.

    This model stores Mercury Bank API credentials and configuration for account groups.
    Each MercuryAccount represents a set of API credentials that can access one or more
    Mercury Bank accounts. Multiple users can be granted access to the same MercuryAccount,
    allowing for flexible permission management and team access to Mercury Bank data.

    The sync process will iterate through all active MercuryAccount records and use their
    API keys to fetch account and transaction data from Mercury Bank.

    Attributes:
        id (str): Primary key - unique identifier for the account group
        name (str): Descriptive name for this account group
        api_key (str): Mercury Bank API key for accessing the accounts
        sandbox_mode (bool): Whether to use Mercury's sandbox environment
        description (str, optional): Additional description or notes
        is_active (bool): Whether this account group should be synced
        last_sync_at (datetime, optional): Timestamp of last successful sync
        sync_enabled (bool): Whether automatic syncing is enabled for this group
        created_at (datetime): Timestamp when record was created
        updated_at (datetime): Timestamp when record was last updated

        users (list): List of User objects that have access to this account group
        accounts (list): List of Account objects associated with this Mercury account group
    """

    __tablename__ = "mercury_accounts"

    # Core identification fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(255), nullable=False)

    # API configuration
    api_key = Column(String(500), nullable=False)  # Mercury API keys can be long
    sandbox_mode = Column(Boolean, default=False)

    # Description and metadata
    description = Column(Text, nullable=True)

    # Status and sync configuration
    is_active = Column(Boolean, default=True)
    sync_enabled = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Many-to-many relationship with User
    users = relationship(
        "User",
        secondary=user_mercury_account_association,
        back_populates="mercury_accounts",
    )

    # One-to-many relationship with Account
    accounts = relationship("Account", back_populates="mercury_account")

    def __repr__(self):
        """
        Return a string representation of the MercuryAccount instance.

        Returns:
            str: A formatted string showing the name and active status
        """
        return f"<MercuryAccount(name='{self.name}', active={self.is_active})>"

    @property
    def masked_api_key(self):
        """
        Get a masked version of the API key for display purposes.

        Returns:
            str: API key with most characters replaced by asterisks
        """
        if not self.api_key:
            return "No API key"
        if len(self.api_key) <= 8:
            return "*" * len(self.api_key)
        return self.api_key[:4] + "*" * (len(self.api_key) - 8) + self.api_key[-4:]
