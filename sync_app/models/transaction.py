from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Text,
    ForeignKey,
    Boolean,
    Integer,
    text,
)
from sqlalchemy.orm import relationship
from .base import Base


class Transaction(Base):
    """
    SQLAlchemy model representing a Mercury Bank transaction.
    
    This model stores detailed transaction information retrieved from the Mercury Bank API,
    including transaction amounts, descriptions, counterparty details, and various metadata.
    Each transaction is associated with a specific account.
    
    Attributes:
        id (str): Primary key - Mercury transaction ID
        account_id (str): Foreign key referencing the associated account
        amount (float): Transaction amount (positive or negative)
        currency (str): Transaction currency, defaults to 'USD'
        
        description (str, optional): General transaction description
        bank_description (str, optional): Bank-specific description
        external_memo (str, optional): External memo field
        note (str, optional): Additional transaction notes
        
        transaction_type (str, optional): Legacy transaction type (debit, credit, etc.)
        kind (str, optional): Mercury-specific transaction kind/category
        status (str, optional): Transaction status (pending, completed, failed, etc.)
        mercury_category (str, optional): Mercury-specific transaction category
        category (str, optional): Legacy category field
        
        counterparty_name (str, optional): Name of the transaction counterparty
        counterparty_nickname (str, optional): Nickname of the counterparty
        counterparty_account (str, optional): Account details of the counterparty
        
        reference_number (str, optional): Transaction reference or confirmation number
        
        posted_at (datetime, optional): When the transaction was posted
        estimated_delivery_date (datetime, optional): Estimated delivery date for transfers
        failed_at (datetime, optional): When the transaction failed (if applicable)
        created_at (datetime): Timestamp when record was created
        updated_at (datetime): Timestamp when record was last updated
        
        reason_for_failure (str, optional): Reason why transaction failed
        has_generated_receipt (bool): Whether a receipt has been generated
        number_of_attachments (int): Number of attachments associated with transaction
        
        account (Account): Related Account object
    """
    __tablename__ = "transactions"

    # Core transaction fields
    id = Column(String(255), primary_key=True)  # Mercury transaction ID
    account_id = Column(String(255), ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")

    # Transaction details
    description = Column(Text, nullable=True)  # General description
    bank_description = Column(Text, nullable=True)  # Bank-specific description
    external_memo = Column(Text, nullable=True)  # External memo
    note = Column(Text, nullable=True)  # Transaction note

    # Transaction metadata
    transaction_type = Column(
        String(100), nullable=True
    )  # debit, credit, etc. (legacy field)
    kind = Column(String(100), nullable=True)  # Mercury transaction kind
    status = Column(String(100), nullable=True)
    mercury_category = Column(String(255), nullable=True)  # Mercury-specific category
    category = Column(String(255), nullable=True)  # Legacy category field

    # Counterparty information
    counterparty_name = Column(String(255), nullable=True)
    counterparty_nickname = Column(String(255), nullable=True)
    counterparty_account = Column(String(255), nullable=True)

    # Reference and tracking
    reference_number = Column(String(255), nullable=True)

    # Dates and timing
    posted_at = Column(DateTime(timezone=True), nullable=True)
    estimated_delivery_date = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Failure information
    reason_for_failure = Column(Text, nullable=True)

    # Additional metadata
    has_generated_receipt = Column(Boolean, default=False)
    number_of_attachments = Column(Integer, default=0)

    # Relationship to account
    account = relationship("Account", back_populates="transactions")

    def __repr__(self):
        """
        Return a string representation of the Transaction instance.
        
        Returns:
            str: A formatted string showing the transaction ID, amount, and description
        """
        return f"<Transaction(id='{self.id}', amount={self.amount}, description='{self.description}')>"
