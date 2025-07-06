from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Boolean,
    text,
    ForeignKey,
    Integer,
    Date,
    Table,
)
from sqlalchemy.orm import relationship
from .base import Base

# Association table for budget and account many-to-many relationship
budget_account_association = Table(
    'budget_accounts',
    Base.metadata,
    Column('budget_id', Integer, ForeignKey('budgets.id'), primary_key=True),
    Column('account_id', String(255), ForeignKey('accounts.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
)


class Budget(Base):
    """
    SQLAlchemy model representing a monthly budget.
    
    Budgets are created by admins and assigned to mercury accounts. Users with 
    "budgets" role and access to the mercury account can view and manage budgets.
    Each budget covers a specific month and can include multiple categories and accounts.
    
    Attributes:
        id (int): Primary key - unique budget identifier
        name (str): Descriptive name for the budget
        mercury_account_id (int): Foreign key to MercuryAccount group
        budget_month (date): The month this budget covers (YYYY-MM-01 format)
        is_active (bool): Whether this budget is active
        created_by_user_id (int): User ID who created this budget
        created_at (datetime): Timestamp when budget was created
        updated_at (datetime): Timestamp when budget was last updated
        
        mercury_account (MercuryAccount): Related MercuryAccount group object
        budget_categories (list): List of BudgetCategory objects for this budget
        accounts (list): List of Account objects included in this budget
    """
    
    __tablename__ = "budgets"
    
    # Core budget fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(255), nullable=False)
    mercury_account_id = Column(Integer, ForeignKey("mercury_accounts.id"), nullable=False)
    budget_month = Column(Date, nullable=False)  # First day of the month (YYYY-MM-01)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )
    
    # Relationships
    mercury_account = relationship("MercuryAccount", back_populates="budgets")
    budget_categories = relationship("BudgetCategory", back_populates="budget", cascade="all, delete-orphan")
    accounts = relationship(
        "Account",
        secondary=budget_account_association,
        back_populates="budgets"
    )
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    
    def __repr__(self):
        return f"<Budget(id={self.id}, name='{self.name}', month={self.budget_month})>"


class BudgetCategory(Base):
    """
    SQLAlchemy model representing a budget category within a budget.
    
    Each budget category defines a spending limit for a specific transaction category
    within a budget period. Progress is tracked by comparing actual transaction amounts
    against the budgeted amount.
    
    Attributes:
        id (int): Primary key - unique budget category identifier
        budget_id (int): Foreign key to Budget
        category_name (str): Transaction category name (matches transaction.mercury_category)
        budgeted_amount (float): The budgeted amount for this category
        is_active (bool): Whether this budget category is active
        created_at (datetime): Timestamp when budget category was created
        updated_at (datetime): Timestamp when budget category was last updated
        
        budget (Budget): Related Budget object
    """
    
    __tablename__ = "budget_categories"
    
    # Core budget category fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    category_name = Column(String(255), nullable=False)
    budgeted_amount = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )
    
    # Relationships
    budget = relationship("Budget", back_populates="budget_categories")
    
    def __repr__(self):
        return f"<BudgetCategory(id={self.id}, category='{self.category_name}', amount={self.budgeted_amount})>"
