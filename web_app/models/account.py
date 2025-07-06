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
from .base import Base, user_account_access
from datetime import datetime


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

    # Current receipt requirements for deposits and charges (separate rules)
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

    # Relationship to receipt policies
    receipt_policies = relationship("ReceiptPolicy", back_populates="account", cascade="all, delete-orphan", lazy="dynamic")

    # Many-to-many relationship with Budgets
    budgets = relationship(
        "Budget",
        secondary="budget_accounts",
        back_populates="accounts"
    )

    # Many-to-many relationship with Users for granular access control
    # Explicit join conditions since user_id doesn't have a foreign key constraint
    authorized_users = relationship(
        "User",
        secondary=user_account_access,
        primaryjoin="Account.id == user_account_access.c.account_id",
        secondaryjoin="User.id == user_account_access.c.user_id",
        back_populates="restricted_accounts",
    )

    def is_receipt_required_for_amount(self, amount, transaction_date=None):
        """
        Check if a receipt is required for a given transaction amount.
        
        Uses separate rules for deposits (positive amounts) and charges (negative amounts).
        If transaction_date is provided, uses the policy in effect at that time.

        Args:
            amount (float): Transaction amount to check
            transaction_date (datetime, optional): Date when transaction was posted

        Returns:
            bool: True if receipt is required, False otherwise
        """
        # If no transaction_date provided, use current policy (from account)
        if transaction_date is None:
            # Determine if this is a deposit or charge
            is_deposit = amount > 0
            
            # Get the appropriate receipt requirement setting
            if is_deposit:
                receipt_required = self.receipt_required_deposits
                receipt_threshold = self.receipt_threshold_deposits
            else:
                receipt_required = self.receipt_required_charges
                receipt_threshold = self.receipt_threshold_charges
            
            # Apply the logic
            if receipt_required == "none":
                return False
            elif receipt_required == "always":
                return True
            elif receipt_required == "threshold":
                return receipt_threshold is not None and abs(amount) >= receipt_threshold
            return False
        
        # Find the policy in effect at the transaction date
        # Using self.receipt_policies might not work in SQLAlchemy session expired context,
        # so we use an explicit query
        from sqlalchemy import and_, or_
        from sqlalchemy.orm import Session
        session = Session.object_session(self)
        
        if session is None:
            # If no session is available, fall back to current account settings
            return self.is_receipt_required_for_amount(amount)
            
        # Import here to avoid circular imports
        from .receipt_policy import ReceiptPolicy
        
        # Find the policy in effect at transaction_date
        policy = (
            session.query(ReceiptPolicy)
            .filter(
                ReceiptPolicy.account_id == self.id,
                ReceiptPolicy.start_date <= transaction_date,
                or_(
                    ReceiptPolicy.end_date.is_(None),
                    ReceiptPolicy.end_date >= transaction_date
                )
            )
            .order_by(ReceiptPolicy.start_date.desc())
            .first()
        )
        
        # If no policy found, fall back to current account settings
        if policy is None:
            # Use current account settings as fallback
            is_deposit = amount > 0
            if is_deposit:
                receipt_required = self.receipt_required_deposits
                receipt_threshold = self.receipt_threshold_deposits
            else:
                receipt_required = self.receipt_required_charges
                receipt_threshold = self.receipt_threshold_charges
        else:
            # Use policy settings
            is_deposit = amount > 0
            if is_deposit:
                receipt_required = policy.receipt_required_deposits
                receipt_threshold = policy.receipt_threshold_deposits
            else:
                receipt_required = policy.receipt_required_charges
                receipt_threshold = policy.receipt_threshold_charges
        
        # Apply the logic
        if receipt_required == "none":
            return False
        elif receipt_required == "always":
            return True
        elif receipt_required == "threshold":
            return receipt_threshold is not None and abs(amount) >= receipt_threshold
        return False

    def get_receipt_status_for_transaction(self, amount, has_attachments, transaction_date=None):
        """
        Get the receipt status for display purposes.

        Args:
            amount (float): Transaction amount
            has_attachments (bool): Whether transaction has attachments
            transaction_date (datetime, optional): When the transaction was posted

        Returns:
            str: Status - 'required_present' (green), 'required_missing' (red),
                 'optional_present' (blue), 'optional_missing' (blank)
        """
        required = self.is_receipt_required_for_amount(amount, transaction_date)

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
        
    def update_receipt_policy(self, receipt_required_deposits, receipt_threshold_deposits, 
                              receipt_required_charges, receipt_threshold_charges, start_date=None):
        """
        Update receipt policy settings and create a historical record.
        
        This method should be called whenever receipt settings are changed to maintain
        a history of policies that apply to different time periods.
        
        Args:
            receipt_required_deposits (str): Receipt requirement for deposits
            receipt_threshold_deposits (float): Threshold amount for deposits
            receipt_required_charges (str): Receipt requirement for charges
            receipt_threshold_charges (float): Threshold amount for charges
            start_date (datetime, optional): The date when the policy should take effect.
                                            If None, the policy will take effect immediately.
            
        Returns:
            None
        """
        from sqlalchemy.orm import Session
        session = Session.object_session(self)
        
        if session is None:
            raise ValueError("Cannot update receipt policy: no active database session")
            
        # Import ReceiptPolicy class
        from .receipt_policy import ReceiptPolicy
        
        # Get the current active policy (if any)
        current_policy = (
            session.query(ReceiptPolicy)
            .filter(
                ReceiptPolicy.account_id == self.id,
                ReceiptPolicy.end_date.is_(None)
            )
            .order_by(ReceiptPolicy.start_date.desc())
            .first()
        )
        
        # Check if there are any changes to receipt settings (and a policy already exists)
        if current_policy and (
                self.receipt_required_deposits == receipt_required_deposits and
                self.receipt_threshold_deposits == receipt_threshold_deposits and
                self.receipt_required_charges == receipt_required_charges and
                self.receipt_threshold_charges == receipt_threshold_charges):
            # No changes, no need to create a new policy
            return
            
        # If there's a current policy, set its end date to start date of new policy
        now = datetime.now()
        effective_date = start_date if start_date else now
        
        if current_policy:
            # Only end the current policy when the new policy takes effect
            current_policy.end_date = effective_date
            
        # Create a new policy with the updated settings
        new_policy = ReceiptPolicy(
            account_id=self.id,
            start_date=effective_date,
            end_date=None,  # Active policy
            receipt_required_deposits=receipt_required_deposits,
            receipt_threshold_deposits=receipt_threshold_deposits,
            receipt_required_charges=receipt_required_charges,
            receipt_threshold_charges=receipt_threshold_charges
        )
        
        # Update the account's current settings 
        # Note: We always update these fields immediately so they're reflected in the UI,
        # even though the actual policy might take effect at a future date
        self.receipt_required_deposits = receipt_required_deposits
        self.receipt_threshold_deposits = receipt_threshold_deposits
        self.receipt_required_charges = receipt_required_charges
        self.receipt_threshold_charges = receipt_threshold_charges
        
        # Add the new policy to the session
        session.add(new_policy)
        
        # The session.commit() should be called by the caller
