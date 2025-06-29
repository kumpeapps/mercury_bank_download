from sqlalchemy import Column, String, DateTime, Float, Boolean, text
from sqlalchemy.orm import relationship
from .base import Base

class Account(Base):
    __tablename__ = 'accounts'
    
    # Required fields based on Mercury Bank API
    id = Column(String(255), primary_key=True)  # Mercury account ID
    name = Column(String(255), nullable=False)
    account_number = Column(String(255), nullable=True)  # Mercury doesn't provide this in API
    routing_number = Column(String(255), nullable=True)
    account_type = Column(String(100), nullable=True)  # Also maps to 'type'
    status = Column(String(100), nullable=True)
    balance = Column(Float, nullable=True)  # Also maps to 'current_balance'
    available_balance = Column(Float, nullable=True)  # Also maps to 'available'
    currency = Column(String(10), default='USD')
    
    # Additional Mercury Bank specific fields
    kind = Column(String(100), nullable=True)  # Account kind from Mercury
    nickname = Column(String(255), nullable=True)  # Account nickname
    legal_business_name = Column(String(255), nullable=True)  # Legal business name
    
    # System fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
    
    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="account")
    
    def __repr__(self):
        return f"<Account(id='{self.id}', name='{self.name}', balance={self.balance})>"
