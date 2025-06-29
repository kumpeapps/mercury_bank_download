from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey, Boolean, Integer, text
from sqlalchemy.orm import relationship
from .base import Base

class Transaction(Base):
    __tablename__ = 'transactions'
    
    # Core transaction fields
    id = Column(String(255), primary_key=True)  # Mercury transaction ID
    account_id = Column(String(255), ForeignKey('accounts.id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    
    # Transaction details
    description = Column(Text, nullable=True)  # General description
    bank_description = Column(Text, nullable=True)  # Bank-specific description
    external_memo = Column(Text, nullable=True)  # External memo
    note = Column(Text, nullable=True)  # Transaction note
    
    # Transaction metadata
    transaction_type = Column(String(100), nullable=True)  # debit, credit, etc. (legacy field)
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
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
    
    # Failure information
    reason_for_failure = Column(Text, nullable=True)
    
    # Additional metadata
    has_generated_receipt = Column(Boolean, default=False)
    number_of_attachments = Column(Integer, default=0)
    
    # Relationship to account
    account = relationship("Account", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id='{self.id}', amount={self.amount}, description='{self.description}')>"
