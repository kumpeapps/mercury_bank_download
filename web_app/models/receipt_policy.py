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


class ReceiptPolicy(Base):
    """
    SQLAlchemy model representing a receipt policy that applies to a specific time period.
    
    This model tracks receipt requirement changes over time, allowing transactions
    to be evaluated based on the policy that was in effect when they were posted.
    
    Attributes:
        id (int): Primary key - Auto-incrementing ID
        account_id (str): Foreign key to Account
        start_date (datetime): When this policy starts applying
        end_date (datetime, optional): When this policy stops applying (NULL means still active)
        receipt_required_deposits (str): Receipt requirement for deposits - 'none', 'always', or 'threshold'
        receipt_threshold_deposits (float, optional): Dollar amount threshold for deposit receipt requirement
        receipt_required_charges (str): Receipt requirement for charges - 'none', 'always', or 'threshold'
        receipt_threshold_charges (float, optional): Dollar amount threshold for charge receipt requirement
        created_at (datetime): Timestamp when record was created
        updated_at (datetime): Timestamp when record was last updated
        account (Account): Related Account object
    """

    __tablename__ = "receipt_policies"

    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(255), ForeignKey("accounts.id"), nullable=False)
    
    # Time period
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)  # NULL means still active
    
    # Receipt policies - same as in Account model
    receipt_required_deposits = Column(String(20), default="none")  # "none", "always", "threshold"
    receipt_threshold_deposits = Column(Float, nullable=True)  # Dollar amount threshold for deposit receipt requirement
    receipt_required_charges = Column(String(20), default="none")  # "none", "always", "threshold"
    receipt_threshold_charges = Column(Float, nullable=True)  # Dollar amount threshold for charge receipt requirement
    
    # System fields
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Relationship to account
    account = relationship("Account", back_populates="receipt_policies")
    
    def is_receipt_required_for_amount(self, amount):
        """
        Check if a receipt is required for a given transaction amount based on this policy.
        
        Uses separate rules for deposits (positive amounts) and charges (negative amounts).

        Args:
            amount (float): Transaction amount to check

        Returns:
            bool: True if receipt is required, False otherwise
        """
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
        
    def __repr__(self):
        """
        Return a string representation of the ReceiptPolicy instance.

        Returns:
            str: A formatted string showing the policy ID, account ID, and date range
        """
        end_date_str = self.end_date.strftime("%Y-%m-%d") if self.end_date else "current"
        return f"<ReceiptPolicy(id={self.id}, account_id='{self.account_id}', period={self.start_date.strftime('%Y-%m-%d')} to {end_date_str})>"
