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
from .transaction_attachment import TransactionAttachment  # Import TransactionAttachment model


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
        attachments (list): List of related TransactionAttachment objects
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
    
    # Approval status
    approval_status = Column(String(50), default=None, nullable=True)  # None, 'approved', 'violation', 'auto_approved'
    approval_id = Column(Integer, nullable=True)  # Reference to TransactionApproval that was used

    # Relationship to account
    account = relationship("Account", back_populates="transactions")

    # Relationship to transaction attachments
    attachments = relationship("TransactionAttachment", back_populates="transaction", cascade="all, delete-orphan")

    def update_approval_status(self, db_session):
        """
        Update approval status for this transaction.
        
        Only applies to charges (negative amounts) with status pending, posted, or sent.
        Excludes failed transactions and deposits from approval processing.
        
        Args:
            db_session: SQLAlchemy database session
        """
        try:
            # Skip transactions that already have an approval status to prevent re-processing
            if self.approval_status is not None:
                return
                
            # Only process charges (negative amounts) with approved statuses
            if self.amount >= 0:  # Skip deposits (positive amounts)
                self.approval_status = None
                self.approval_id = None
                return
                
            if self.status not in ['pending', 'posted', 'sent']:  # Skip failed and other statuses
                self.approval_status = None
                self.approval_id = None
                return
            
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from simple_timezone_fix import make_naive
            from transaction_approval_manager import TransactionApprovalManager
            from category_utils import parse_category
            
            approval_manager = TransactionApprovalManager(db_session)
            
            # Use created_at (actual transaction date) instead of posted_at
            transaction_date = None
            if self.created_at:
                transaction_date = make_naive(self.created_at)
            
            # Parse category and subcategory from note field (same as rest of system)
            category, subcategory = parse_category(self.note)
            
            # Use the new method that tracks cumulative spending
            status, approval_id = approval_manager.check_and_update_transaction_approval_status(
                str(self.id),  # Pass transaction ID for usage tracking
                self.account_id, 
                abs(self.amount),  # Use absolute value for amount checks
                category,  # Use parsed category from note field
                subcategory,  # Use parsed subcategory from note field
                self.counterparty_name,  # Pass counterparty name as merchant
                transaction_date  # Pass timezone-naive transaction date
            )
            
            self.approval_status = status
            self.approval_id = approval_id
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            
            # Get more detailed error information
            import traceback
            error_details = traceback.format_exc()
            
            logger.warning(f"Failed to update approval status for transaction {self.id}: {str(e)}")
            logger.debug(f"Full error traceback: {error_details}")
            
            # Set default values to prevent transaction save failure
            self.approval_status = None
            self.approval_id = None

    def __repr__(self):
        """
        Return a string representation of the Transaction instance.
        
        Returns:
            str: A formatted string showing the transaction ID, amount, and description
        """
        return f"<Transaction(id='{self.id}', amount={self.amount}, description='{self.description}')>"
