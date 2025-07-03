from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Boolean,
    text,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship
from .base import Base


class Account(Base):
    """
    SQLAlchemy model representing a Mercury Bank account.

    This model stores account information retrieved from the Mercury Bank API,
    including account details, balances, and metadata. Each account can have
    multiple associated transactions and belongs to a Mercury account group.

    Attributes:
        user_id (str, optional): Internal user identifier
        mercury_account_id (str, optional): Foreign key to MercuryAccount group
        id (str): Primary key - Mercury account ID
        name (str): Account name/title
        account_number (str, optional): Account number (not provided by Mercury API)
        routing_number (str, optional): Bank routing number
        account_type (str, optional): Type of account (checking, savings, etc.)
        status (str, optional): Account status (active, inactive, etc.)
        balance (float, optional): Current account balance
        available_balance (float, optional): Available balance for transactions
        currency (str): Account currency, defaults to 'USD'
        kind (str, optional): Mercury-specific account kind/category
        nickname (str, optional): User-defined account nickname
        legal_business_name (str, optional): Legal business name associated with account
        receipt_required (str): Legacy receipt requirement setting - 'none', 'always', or 'threshold'
        receipt_threshold (float, optional): Legacy dollar amount threshold for receipt requirement
        receipt_required_deposits (str): Receipt requirement for deposits - 'none', 'always', or 'threshold'
        receipt_threshold_deposits (float, optional): Dollar amount threshold for deposit receipt requirement
        receipt_required_charges (str): Receipt requirement for charges - 'none', 'always', or 'threshold'
        receipt_threshold_charges (float, optional): Dollar amount threshold for charge receipt requirement
        exclude_from_reports (bool): Whether to exclude from reports and "all accounts" filter, defaults to False
        is_active (bool): Whether the account is active, defaults to True
        created_at (datetime): Timestamp when record was created
        updated_at (datetime): Timestamp when record was last updated
        transactions (list): Related Transaction objects
        mercury_account (MercuryAccount): Related MercuryAccount group object
    """

    __tablename__ = "accounts"

    # Required fields based on Mercury Bank API
    mercury_account_id = Column(
        Integer, ForeignKey("mercury_accounts.id"), nullable=True
    )  # Link to Mercury account group
    id = Column(String(255), primary_key=True)  # Mercury account ID
    name = Column(String(255), nullable=False)
    account_number = Column(
        String(255), nullable=True
    )  # Mercury doesn't provide this in API
    routing_number = Column(String(255), nullable=True)
    account_type = Column(String(100), nullable=True)  # Also maps to 'type'
    status = Column(String(100), nullable=True)
    balance = Column(Float, nullable=True)  # Also maps to 'current_balance'
    available_balance = Column(Float, nullable=True)  # Also maps to 'available'
    currency = Column(String(10), default="USD")

    # Additional Mercury Bank specific fields
    kind = Column(String(100), nullable=True)  # Account kind from Mercury
    nickname = Column(String(255), nullable=True)  # Account nickname
    legal_business_name = Column(String(255), nullable=True)  # Legal business name

    # Receipt requirement settings
    receipt_required = Column(String(20), default="none")  # "none", "always", "threshold"
    receipt_threshold = Column(Float, nullable=True)  # Dollar amount threshold for receipt requirement
    
    # Separate receipt requirements for deposits and charges
    receipt_required_deposits = Column(String(20), default="none")  # "none", "always", "threshold"
    receipt_threshold_deposits = Column(Float, nullable=True)  # Dollar amount threshold for deposit receipt requirement
    receipt_required_charges = Column(String(20), default="none")  # "none", "always", "threshold"
    receipt_threshold_charges = Column(Float, nullable=True)  # Dollar amount threshold for charge receipt requirement

    # Report visibility settings
    exclude_from_reports = Column(Boolean, default=False)  # Whether to exclude from reports and "all accounts" filter

    # System fields
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="account")

    # Relationship to mercury account group
    mercury_account = relationship("MercuryAccount", back_populates="accounts")

    def is_receipt_required_for_amount(self, amount):
        """
        Check if a receipt is required for a given transaction amount.
        
        Uses separate rules for deposits (positive amounts) and charges (negative amounts).
        Falls back to the original receipt_required setting if separate settings are not configured.

        Args:
            amount (float): Transaction amount to check

        Returns:
            bool: True if receipt is required, False otherwise
        """
        # Determine if this is a deposit or charge
        is_deposit = amount > 0
        
        # Get the appropriate receipt requirement setting
        if is_deposit:
            receipt_required = self.receipt_required_deposits or self.receipt_required
            receipt_threshold = self.receipt_threshold_deposits or self.receipt_threshold
        else:
            receipt_required = self.receipt_required_charges or self.receipt_required
            receipt_threshold = self.receipt_threshold_charges or self.receipt_threshold
        
        # Apply the logic
        if receipt_required == "none":
            return False
        elif receipt_required == "always":
            return True
        elif receipt_required == "threshold":
            return receipt_threshold is not None and abs(amount) >= receipt_threshold
        return False

    def get_receipt_status_for_transaction(self, amount, has_attachments):
        """
        Get the receipt status for display purposes.

        Args:
            amount (float): Transaction amount
            has_attachments (bool): Whether transaction has attachments

        Returns:
            str: Status - 'required_present' (green), 'required_missing' (red),
                 'optional_present' (blue), 'optional_missing' (blank)
        """
        required = self.is_receipt_required_for_amount(amount)

        if required and has_attachments:
            return "required_present"  # Green
        elif required and not has_attachments:
            return "required_missing"  # Red
        elif not required and has_attachments:
            return "optional_present"  # Blue
        else:
            return "optional_missing"  # Blank

    def __repr__(self):
        """
        Return a string representation of the Account instance.

        Returns:
            str: A formatted string showing the account ID, name, and balance
        """
        return f"<Account(id='{self.id}', name='{self.name}', balance={self.balance})>"
