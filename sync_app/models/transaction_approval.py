"""Transaction approval models for transaction pre-approval workflow."""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, ForeignKey, text
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simple_timezone_fix import get_naive_now, make_naive, naive_datetime_comparison, normalize_for_db_query


class TransactionRestriction(Base):
    """
    SQLAlchemy model representing transaction approval restrictions for accounts.
    
    This model defines rules for which transactions require pre-approval for specific
    Mercury Bank accounts. Admins can set up restrictions by transaction amount, category,
    sub-category, or apply to all transactions. Each restriction has start/end dates
    and designates who can approve requests.
    
    Attributes:
        id (int): Primary key - unique restriction identifier
        name (str): User-defined name for this restriction
        account_ids (str): Comma-separated list of account IDs this restriction applies to
        mercury_account_id (int): Foreign key to the Mercury account group
        restriction_type (str): Type of restriction - 'all', 'amount', 'category', 'subcategory'
        amount_threshold (float, optional): Minimum amount that requires approval (for amount type)
        category (str, optional): Category that requires approval (for category type)
        subcategory (str, optional): Sub-category that requires approval (for subcategory type)
        approvers (str): Comma-separated list of user IDs who can approve requests
        start_date (datetime): When this restriction becomes active
        end_date (datetime, optional): When this restriction expires (null = no expiration)
        is_active (bool): Whether this restriction is currently active
        created_by_user_id (int): User who created this restriction
        created_at (datetime): When this restriction was created
        updated_at (datetime): When this restriction was last updated
    """
    
    __tablename__ = "transaction_restrictions"
    
    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(255), nullable=False)  # User-defined name for the restriction
    account_ids = Column(Text, nullable=False)  # Comma-separated list of account IDs
    mercury_account_id = Column(Integer, ForeignKey("mercury_accounts.id"), nullable=False)
    
    # Restriction configuration
    restriction_type = Column(String(50), nullable=False)  # 'all', 'amount', 'category', 'subcategory'
    amount_threshold = Column(Float, nullable=True)  # For amount-based restrictions
    category = Column(String(255), nullable=True)  # For category-based restrictions
    subcategory = Column(String(255), nullable=True)  # For subcategory-based restrictions
    
    # Approval configuration
    approvers = Column(Text, nullable=False)  # Comma-separated user IDs
    
    # Date range
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)  # Null = no expiration
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    mercury_account = relationship("MercuryAccount", back_populates="transaction_restrictions")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    approval_requests = relationship("TransactionApprovalRequest", back_populates="restriction", cascade="all, delete-orphan")
    
    def get_account_list(self):
        """Get list of account IDs this restriction applies to."""
        if not self.account_ids:
            return []
        return [aid.strip() for aid in self.account_ids.split(',') if aid.strip()]
    
    def set_accounts(self, account_ids):
        """Set accounts from list of account IDs."""
        self.account_ids = ','.join(str(aid) for aid in account_ids)
    
    def get_account_names(self, db_session):
        """Get display names for all accounts this restriction applies to."""
        from .account import Account
        account_ids = self.get_account_list()
        if not account_ids:
            return []
        
        accounts = db_session.query(Account).filter(Account.id.in_(account_ids)).all()
        return [acc.nickname if acc.nickname else acc.name for acc in accounts]
    
    def applies_to_account(self, account_id):
        """Check if this restriction applies to a specific account."""
        return account_id in self.get_account_list()
    
    def get_approver_list(self):
        """Get list of approver user IDs."""
        if not self.approvers:
            return []
        return [int(uid.strip()) for uid in self.approvers.split(',') if uid.strip().isdigit()]
    
    def set_approvers(self, user_ids):
        """Set approvers from list of user IDs."""
        self.approvers = ','.join(str(uid) for uid in user_ids)
    
    def is_active_now(self):
        """Check if restriction is active at current time."""
        now = get_naive_now()
        if not self.is_active:
            return False

        # Use timezone-naive comparison
        if naive_datetime_comparison(now, '<', make_naive(self.start_date)):
            return False
            
        if self.end_date:
            if naive_datetime_comparison(now, '>', make_naive(self.end_date)):
                return False
        return True

    def applies_to_transaction(self, account_id, amount, category=None, subcategory=None, transaction_date=None):
        """Check if this restriction applies to a transaction."""
        if not self.is_active_now():
            return False
        
        # Check if restriction applies to this account
        if not self.applies_to_account(account_id):
            return False
        
        # Check if transaction occurred after restriction start date
        if transaction_date:
            # Use timezone-naive comparison
            if naive_datetime_comparison(make_naive(transaction_date), '<', make_naive(self.start_date)):
                return False
            
        if self.restriction_type == 'all' or self.restriction_type == 'all_transactions':
            return True
        elif self.restriction_type == 'amount':
            return abs(amount) >= (self.amount_threshold or 0)
        elif self.restriction_type == 'category':
            return category and category.lower() == (self.category or '').lower()
        elif self.restriction_type == 'subcategory':
            return subcategory and subcategory.lower() == (self.subcategory or '').lower()
        
        return False


class TransactionApprovalRequest(Base):
    """
    SQLAlchemy model representing a request for transaction approval.
    
    Users submit these requests when they need approval for transactions that
    fall under restrictions. Each request specifies limits on number of transactions,
    total dollar amount, timeframe, and optional category/subcategory filters.
    
    Attributes:
        id (int): Primary key - unique request identifier
        restriction_id (int): Foreign key to the restriction that triggered this request
        requested_by_user_id (int): User who submitted the request
        max_transactions (int, optional): Maximum number of transactions to approve
        max_amount (float, optional): Maximum total dollar amount to approve
        approval_start_date (datetime): When approved transactions can start
        approval_end_date (datetime): When approved transactions must end by
        category_filter (str, optional): Limit approval to specific category
        subcategory_filter (str, optional): Limit approval to specific subcategory
        request_reason (text, optional): User's reason for the request
        status (str): Current status - 'pending', 'approved', 'denied', 'expired'
        approved_by_user_id (int, optional): User who approved/denied the request
        approval_decision_date (datetime, optional): When the decision was made
        approval_notes (text, optional): Notes from approver
        created_at (datetime): When this request was created
        updated_at (datetime): When this request was last updated
    """
    
    __tablename__ = "transaction_approval_requests"
    
    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    restriction_id = Column(Integer, ForeignKey("transaction_restrictions.id"), nullable=False)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Request parameters
    max_transactions = Column(Integer, nullable=True)  # Null = unlimited
    max_amount = Column(Float, nullable=True)  # Null = unlimited
    approval_start_date = Column(DateTime(timezone=True), nullable=False)
    approval_end_date = Column(DateTime(timezone=True), nullable=False)
    category_filter = Column(String(255), nullable=True)  # Null = any category
    subcategory_filter = Column(String(255), nullable=True)  # Null = any subcategory
    merchant_filter = Column(String(255), nullable=True)  # Null = any merchant (based on counterparty_name)
    request_reason = Column(Text, nullable=True)
    
    # Approval status
    status = Column(String(50), default='pending', nullable=False)  # 'pending', 'approved', 'denied', 'expired'
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_decision_date = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    restriction = relationship("TransactionRestriction", back_populates="approval_requests")
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    approvals = relationship("TransactionApproval", back_populates="request", cascade="all, delete-orphan")
    
    def is_expired(self):
        """Check if this request has expired."""
        now = get_naive_now()
        
        # Use timezone-naive comparison
        return naive_datetime_comparison(now, '>', make_naive(self.approval_end_date))
    
    def can_be_used(self):
        """Check if this approved request can still be used."""
        now = get_naive_now()
        
        # Use timezone-naive comparison
        return (self.status == 'approved' and 
                not self.is_expired() and
                naive_datetime_comparison(now, '>=', make_naive(self.approval_start_date)))


class TransactionApproval(Base):
    """
    SQLAlchemy model representing an active transaction approval.
    
    When an approval request is approved, this model tracks the usage of that approval.
    As transactions are processed and match the approval criteria, the used amounts
    and transaction counts are updated until the limits are reached.
    
    Attributes:
        id (int): Primary key - unique approval identifier
        request_id (int): Foreign key to the original approval request
        account_id (str): Foreign key to the account this approval applies to
        max_transactions (int, optional): Maximum number of transactions approved
        max_amount (float, optional): Maximum total dollar amount approved
        used_transactions (int): Number of transactions already used
        used_amount (float): Total dollar amount already used
        approval_start_date (datetime): When this approval becomes valid
        approval_end_date (datetime): When this approval expires
        category_filter (str, optional): Category restriction for this approval
        subcategory_filter (str, optional): Subcategory restriction for this approval
        is_active (bool): Whether this approval is currently active
        created_at (datetime): When this approval was created
        updated_at (datetime): When this approval was last updated
    """
    
    __tablename__ = "transaction_approvals"
    
    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    request_id = Column(Integer, ForeignKey("transaction_approval_requests.id"), nullable=False)
    account_id = Column(String(255), ForeignKey("accounts.id"), nullable=False)
    
    # Approval limits
    max_transactions = Column(Integer, nullable=True)  # Null = unlimited
    max_amount = Column(Float, nullable=True)  # Null = unlimited
    
    # Usage tracking
    used_transactions = Column(Integer, default=0, nullable=False)
    used_amount = Column(Float, default=0.0, nullable=False)
    
    # Validity period
    approval_start_date = Column(DateTime(timezone=True), nullable=False)
    approval_end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Filters
    category_filter = Column(String(255), nullable=True)
    subcategory_filter = Column(String(255), nullable=True)
    merchant_filter = Column(String(255), nullable=True)  # Based on counterparty_name
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    request = relationship("TransactionApprovalRequest", back_populates="approvals")
    account = relationship("Account", back_populates="transaction_approvals")
    transaction_logs = relationship("TransactionApprovalLog", back_populates="approval", cascade="all, delete-orphan")
    
    def can_approve_transaction(self, amount, category=None, subcategory=None, merchant=None, transaction_date=None):
        """Check if this approval can be used for a transaction."""
        if not self.is_active:
            return False
            
        # Use transaction date if provided, otherwise use current time
        check_date = transaction_date if transaction_date else get_naive_now()
        
        # Ensure check_date is timezone-naive
        check_date = make_naive(check_date)
        
        try:
            # Use timezone-naive comparison with additional safety
            start_date_naive = make_naive(self.approval_start_date)
            end_date_naive = make_naive(self.approval_end_date)
            
            if (naive_datetime_comparison(check_date, '<', start_date_naive) or 
                naive_datetime_comparison(check_date, '>', end_date_naive)):
                return False
        except Exception as e:
            # Fallback to direct comparison if timezone helper fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Timezone comparison failed, using fallback: {str(e)}")
            
            # Try direct comparison after making everything naive
            try:
                start_naive = self.approval_start_date.replace(tzinfo=None) if self.approval_start_date.tzinfo else self.approval_start_date
                end_naive = self.approval_end_date.replace(tzinfo=None) if self.approval_end_date.tzinfo else self.approval_end_date
                check_naive = check_date.replace(tzinfo=None) if check_date.tzinfo else check_date
                
                if check_naive < start_naive or check_naive > end_naive:
                    return False
            except Exception as e2:
                logger.error(f"Fallback comparison also failed: {str(e2)}")
                return False
        
        # Check transaction count limit
        if self.max_transactions is not None and self.used_transactions >= self.max_transactions:
            return False
        
        # Check amount limit
        if self.max_amount is not None and (self.used_amount + abs(amount)) > self.max_amount:
            return False
        
        # Check category filters
        if self.category_filter and category:
            if category.lower() != self.category_filter.lower():
                return False
        
        if self.subcategory_filter and subcategory:
            if subcategory.lower() != self.subcategory_filter.lower():
                return False
        
        # Check merchant filter (based on counterparty_name)
        if self.merchant_filter and merchant:
            if merchant.lower() != self.merchant_filter.lower():
                return False
        
        return True
    
    def use_for_transaction(self, transaction_id, amount):
        """Mark this approval as used for a transaction."""
        self.used_transactions += 1
        self.used_amount += abs(amount)
        
        # Create log entry
        log = TransactionApprovalLog(
            approval_id=self.id,
            transaction_id=transaction_id,
            amount=amount,
            used_at=get_naive_now()
        )
        self.transaction_logs.append(log)
        
        # Check if approval is fully used
        if ((self.max_transactions is not None and self.used_transactions >= self.max_transactions) or
            (self.max_amount is not None and self.used_amount >= self.max_amount)):
            self.is_active = False


class TransactionApprovalRule(Base):
    """
    SQLAlchemy model representing automatic approval rules.
    
    Admins can create rules that automatically approve certain transactions without
    requiring manual approval. Rules are processed in priority order and can be
    based on amount, category, subcategory, or other criteria.
    
    Attributes:
        id (int): Primary key - unique rule identifier
        account_id (str): Foreign key to the account this rule applies to
        mercury_account_id (int): Foreign key to the Mercury account group
        rule_name (str): Descriptive name for this rule
        priority (int): Processing priority (lower numbers processed first)
        rule_type (str): Type of rule - 'amount', 'category', 'subcategory', 'always'
        amount_threshold (float, optional): Auto-approve if amount is below this
        category (str, optional): Auto-approve if category matches
        subcategory (str, optional): Auto-approve if subcategory matches
        start_date (datetime): When this rule becomes active
        end_date (datetime, optional): When this rule expires
        is_active (bool): Whether this rule is currently active
        created_by_user_id (int): User who created this rule
        created_at (datetime): When this rule was created
        updated_at (datetime): When this rule was last updated
    """
    
    __tablename__ = "transaction_approval_rules"
    
    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    account_id = Column(String(255), ForeignKey("accounts.id"), nullable=False)
    mercury_account_id = Column(Integer, ForeignKey("mercury_accounts.id"), nullable=False)
    
    # Rule configuration
    rule_name = Column(String(255), nullable=False)
    priority = Column(Integer, default=1000, nullable=False)  # Lower = higher priority
    rule_type = Column(String(50), nullable=False)  # 'amount', 'category', 'subcategory', 'always'
    amount_threshold = Column(Float, nullable=True)  # For amount-based rules
    category = Column(String(255), nullable=True)  # For category-based rules
    subcategory = Column(String(255), nullable=True)  # For subcategory-based rules
    
    # Date range
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    account = relationship("Account", back_populates="approval_rules")
    mercury_account = relationship("MercuryAccount", back_populates="approval_rules")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    
    def is_active_now(self):
        """Check if rule is active at current time."""
        now = get_naive_now()
        if not self.is_active:
            return False
            
        # Use timezone-naive comparison
        if naive_datetime_comparison(now, '<', make_naive(self.start_date)):
            return False
            
        if self.end_date:
            if naive_datetime_comparison(now, '>', make_naive(self.end_date)):
                return False
                
        return True
    
    def applies_to_transaction(self, amount, category=None, subcategory=None):
        """Check if this rule automatically approves a transaction."""
        if not self.is_active_now():
            return False
            
        if self.rule_type == 'always':
            return True
        elif self.rule_type == 'amount':
            return abs(amount) <= (self.amount_threshold or 0)
        elif self.rule_type == 'category':
            return category and category.lower() == (self.category or '').lower()
        elif self.rule_type == 'subcategory':
            return subcategory and subcategory.lower() == (self.subcategory or '').lower()
        
        return False


class TransactionApprovalLog(Base):
    """
    SQLAlchemy model representing a log of approval usage.
    
    This model tracks when approvals are used for specific transactions,
    providing an audit trail of approval usage.
    
    Attributes:
        id (int): Primary key - unique log identifier
        approval_id (int): Foreign key to the approval that was used
        transaction_id (str): ID of the transaction that was approved
        amount (float): Amount of the approved transaction
        used_at (datetime): When the approval was used
    """
    
    __tablename__ = "transaction_approval_logs"
    
    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    approval_id = Column(Integer, ForeignKey("transaction_approvals.id"), nullable=False)
    transaction_id = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    approval = relationship("TransactionApproval", back_populates="transaction_logs")


class NotificationLog(Base):
    """
    SQLAlchemy model representing sent notifications.
    
    This model tracks all notifications sent by the system for audit purposes
    and to prevent duplicate notifications.
    
    Attributes:
        id (int): Primary key - unique notification identifier
        notification_type (str): Type of notification - 'approval_request', 'approval_decision', 'transaction_blocked'
        recipient_type (str): Type of recipient - 'email', 'pushover'
        recipient_address (str): Email address or Pushover user key
        subject (str): Notification subject/title
        message (text): Notification content
        related_id (int, optional): ID of related record (request, approval, etc.)
        status (str): Send status - 'sent', 'failed', 'pending'
        sent_at (datetime, optional): When notification was sent
        error_message (text, optional): Error details if send failed
        created_at (datetime): When notification was queued
    """
    
    __tablename__ = "notification_logs"
    
    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    notification_type = Column(String(100), nullable=False)
    recipient_type = Column(String(50), nullable=False)  # 'email', 'pushover'
    recipient_address = Column(String(500), nullable=False)
    
    # Message content
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    
    # Context
    related_id = Column(Integer, nullable=True)
    related_type = Column(String(100), nullable=True)  # 'approval_request', 'approval', etc.
    
    # Status
    status = Column(String(50), default='pending', nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
