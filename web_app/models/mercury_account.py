from sqlalchemy import Column, String, DateTime, Boolean, Text, text, Integer
from sqlalchemy.orm import relationship
from .base import Base, user_mercury_account_association
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.encryption import encrypt_api_key, decrypt_api_key


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
        api_key (str): Mercury Bank API key for accessing the accounts - encrypted at rest
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

    # API configuration - encrypted storage
    _api_key_encrypted = Column("api_key", String(500), nullable=False)
    sandbox_mode = Column(Boolean, default=False)

    @property
    def api_key(self):
        """
        Get the decrypted API key.
        
        Returns:
            str: Decrypted API key
        """
        if not self._api_key_encrypted:
            return None
        try:
            return decrypt_api_key(self._api_key_encrypted)
        except ValueError:
            # If decryption fails, assume it's a legacy unencrypted key
            # This allows for graceful migration from unencrypted to encrypted storage
            return self._api_key_encrypted
    
    @api_key.setter
    def api_key(self, value):
        """
        Set the API key (will be encrypted before storage).
        
        Args:
            value (str): Plain text API key to encrypt and store
        """
        if value is None:
            self._api_key_encrypted = None
        else:
            # Check if the value is already encrypted (for migration scenarios)
            try:
                # Try to decrypt it first - if it works, it's already encrypted
                decrypt_api_key(value)
                self._api_key_encrypted = value
            except ValueError:
                # If decryption fails, it's a plain text key that needs encryption
                self._api_key_encrypted = encrypt_api_key(value)

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

    # One-to-many relationship with Account
    accounts = relationship("Account", back_populates="mercury_account")

    # One-to-many relationship with Budget
    budgets = relationship("Budget", back_populates="mercury_account")

    # Many-to-many relationship with User
    users = relationship(
        "User",
        secondary=user_mercury_account_association,
        back_populates="mercury_accounts"
    )

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
        api_key = self.api_key  # This will decrypt the key
        if not api_key:
            return "No API key"
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

    def get_decrypted_api_key(self):
        """
        Explicit method to get decrypted API key for use in sync operations.
        
        Returns:
            str: Decrypted API key
        """
        return self.api_key

    def set_api_key(self, api_key):
        """
        Explicit method to set and encrypt API key.
        
        Args:
            api_key (str): Plain text API key to encrypt and store
        """
        self.api_key = api_key
