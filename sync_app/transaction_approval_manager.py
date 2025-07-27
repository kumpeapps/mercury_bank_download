"""Transaction approval logic for checking and processing approvals."""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from models import (
    TransactionRestriction,
    TransactionApprovalRequest,
    TransactionApproval,
    TransactionApprovalRule,
    TransactionApprovalLog,
    NotificationLog,
    Account,
    User,
    MercuryAccount
)
from notification_service import notification_service
from simple_timezone_fix import get_naive_now, make_naive, normalize_for_db_query, naive_datetime_comparison
import logging

logger = logging.getLogger(__name__)


class TransactionApprovalManager:
    """Manages transaction approval logic and workflow."""
    
    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
    
    def check_transaction_approval_status(self, account_id: str, amount: float, 
                                        category: Optional[str] = None, 
                                        subcategory: Optional[str] = None,
                                        merchant: Optional[str] = None,
                                        transaction_date: Optional[datetime] = None) -> Tuple[str, Optional[int]]:
        """
        Check if a transaction requires approval and its current status.
        
        Args:
            account_id: Account ID for the transaction
            amount: Transaction amount
            category: Transaction category (optional)
            subcategory: Transaction subcategory (optional)
            transaction_date: Transaction date (optional)
            
        Returns:
            Tuple of (status, approval_id) where status is one of:
            - 'not_required': No approval required
            - 'approved': Required approval and has valid approval
            - 'violation': Required approval but no approval available
            - 'auto_approved': Automatically approved by rule
            And approval_id is the ID of the approval used (if any)
        """
        # First check if there are any active restrictions for this account
        restrictions = self.get_active_restrictions(account_id)
        
        if not restrictions:
            # No restrictions = no approval required
            return 'not_required', None
        
        # Check if any restrictions apply to this transaction
        applicable_restrictions = []
        for restriction in restrictions:
            if restriction.applies_to_transaction(account_id, amount, category, subcategory, transaction_date):
                applicable_restrictions.append(restriction)
        
        if not applicable_restrictions:
            # No applicable restrictions = no approval required
            return 'not_required', None
        
        # Transaction requires approval - check for existing approvals
        
        # Check for auto-approval rules (processed in priority order)
        auto_approval_rule = self.check_auto_approval_rules(account_id, amount, category, subcategory)
        if auto_approval_rule:
            logger.info(f"Transaction auto-approved by rule: {auto_approval_rule.rule_name}")
            return 'auto_approved', None
        
        # Check for existing approvals that can cover this transaction
        approval = self.find_usable_approval(account_id, amount, category, subcategory, merchant, transaction_date)
        if approval:
            return 'approved', approval.id
        
        # Transaction requires approval but has none - violation
        return 'violation', None
    
    def check_and_update_transaction_approval_status(self, transaction_id: str, account_id: str, amount: float, 
                                                   category: Optional[str] = None, 
                                                   subcategory: Optional[str] = None,
                                                   merchant: Optional[str] = None,
                                                   transaction_date: Optional[datetime] = None) -> Tuple[str, Optional[int]]:
        """
        Check transaction approval status and update approval usage if approved.
        
        This method handles the cumulative spending tracking by:
        1. Checking if approval is required
        2. Finding a usable approval
        3. If found, marking it as used for this transaction
        
        Args:
            transaction_id: Unique transaction identifier
            account_id: Account ID for the transaction
            amount: Transaction amount
            category: Transaction category (optional)
            subcategory: Transaction subcategory (optional)
            transaction_date: Transaction date (optional)
            
        Returns:
            Tuple of (status, approval_id) where status is one of:
            - 'not_required': No approval required
            - 'approved': Required approval and has valid approval (approval usage updated)
            - 'violation': Required approval but no approval available
            - 'auto_approved': Automatically approved by rule
            And approval_id is the ID of the approval used (if any)
        """
        # First check basic approval status without usage tracking
        status, approval_id = self.check_transaction_approval_status(
            account_id, amount, category, subcategory, merchant, transaction_date
        )
        
        # If transaction is approved via a specific approval, update usage tracking
        if status == 'approved' and approval_id:
            try:
                approval = self.db.query(TransactionApproval).filter(
                    TransactionApproval.id == approval_id
                ).first()
                
                if approval:
                    # Double-check that approval can still handle this transaction with current usage
                    if approval.can_approve_transaction(amount, category, subcategory, merchant, transaction_date):
                        # Mark approval as used for this transaction
                        approval.use_for_transaction(transaction_id, amount)
                        self.db.commit()
                        logger.info(f"Transaction {transaction_id} approved using approval {approval_id}. Used: {approval.used_amount:.2f}/{approval.max_amount:.2f}")
                        return 'approved', approval_id
                    else:
                        # Approval limit would be exceeded
                        logger.info(f"Transaction {transaction_id} exceeds approval {approval_id} limits")
                        return 'violation', None
                else:
                    logger.error(f"Approval {approval_id} not found for transaction {transaction_id}")
                    return 'violation', None
                    
            except Exception as e:
                logger.error(f"Failed to update approval usage for transaction {transaction_id}: {str(e)}")
                self.db.rollback()
                return 'violation', None
        
        # Return original status for non-approval cases
        return status, approval_id
    
    def reset_and_recalculate_approval_usage(self, account_id: str = None):
        """
        Reset approval usage counters and recalculate based on approved transactions.
        
        This ensures that approval limits are properly enforced by processing
        all approved transactions in chronological order.
        
        Args:
            account_id: If specified, only reset approvals for this account
        """
        try:
            # Get all active approvals (optionally filtered by account)
            query = self.db.query(TransactionApproval).filter(
                TransactionApproval.is_active == True
            )
            if account_id:
                query = query.filter(TransactionApproval.account_id == account_id)
            
            approvals = query.all()
            
            # Reset all approval usage counters
            for approval in approvals:
                approval.used_amount = 0.0
                approval.used_transactions = 0
                
                # Clear existing logs for this approval
                self.db.query(TransactionApprovalLog).filter(
                    TransactionApprovalLog.approval_id == approval.id
                ).delete()
            
            self.db.commit()
            
            # Import here to avoid circular imports
            from models.transaction import Transaction
            
            # Get all approved transactions for the account(s), ordered by date
            transaction_query = self.db.query(Transaction).filter(
                Transaction.approval_status == 'approved',
                Transaction.approval_id.isnot(None)
            )
            if account_id:
                transaction_query = transaction_query.filter(Transaction.account_id == account_id)
            
            # Order by created_at to process transactions chronologically
            approved_transactions = transaction_query.order_by(Transaction.created_at.asc()).all()
            
            # Re-process each approved transaction in chronological order
            for transaction in approved_transactions:
                try:
                    approval = self.db.query(TransactionApproval).filter(
                        TransactionApproval.id == transaction.approval_id
                    ).first()
                    
                    if approval and approval.is_active:
                        # Recalculate if this transaction can still be approved
                        if approval.can_approve_transaction(
                            abs(transaction.amount), 
                            transaction.category, 
                            transaction.mercury_category,
                            transaction.counterparty_name,
                            transaction.created_at
                        ):
                            # Re-add this transaction to the approval usage
                            approval.use_for_transaction(str(transaction.id), abs(transaction.amount))
                        else:
                            # Transaction can no longer be approved - mark as violation
                            transaction.approval_status = 'violation'
                            transaction.approval_id = None
                            logger.warning(f"Transaction {transaction.id} no longer fits approval limits, marked as violation")
                            
                except Exception as e:
                    logger.error(f"Failed to recalculate approval for transaction {transaction.id}: {str(e)}")
                    continue
            
            self.db.commit()
            logger.info(f"Reset and recalculated approval usage for {len(approvals)} approvals and {len(approved_transactions)} transactions")
            
        except Exception as e:
            logger.error(f"Failed to reset and recalculate approval usage: {str(e)}")
            self.db.rollback()
            raise
    
    def get_active_restrictions(self, account_id: str) -> List[TransactionRestriction]:
        """Get all active restrictions for an account."""
        now = normalize_for_db_query(get_naive_now())
        
        # Get all active restrictions without date filtering to avoid timezone issues
        restrictions = self.db.query(TransactionRestriction).filter(
            TransactionRestriction.is_active == True
        ).all()
        
        # Filter restrictions by date range and account manually
        applicable_restrictions = []
        for restriction in restrictions:
            try:
                # Convert dates to naive for comparison
                start_naive = make_naive(restriction.start_date)
                end_naive = make_naive(restriction.end_date) if restriction.end_date else None
                now_naive = make_naive(now)
                
                # Check if restriction is currently active (date range)
                is_date_active = (start_naive <= now_naive and 
                                (end_naive is None or now_naive < end_naive))
                
                if is_date_active and restriction.applies_to_account(account_id):
                    applicable_restrictions.append(restriction)
            except Exception as e:
                logger.warning(f"Date comparison failed for restriction {restriction.id}: {str(e)}")
                continue
        
        return applicable_restrictions
    
    def check_auto_approval_rules(self, account_id: str, amount: float, 
                                category: Optional[str] = None, 
                                subcategory: Optional[str] = None) -> Optional[TransactionApprovalRule]:
        """Check if any auto-approval rules apply to this transaction."""
        now = normalize_for_db_query(get_naive_now())
        rules = self.db.query(TransactionApprovalRule).filter(
            TransactionApprovalRule.account_id == account_id,
            TransactionApprovalRule.is_active == True,
            TransactionApprovalRule.start_date <= now,
            (TransactionApprovalRule.end_date.is_(None) | (TransactionApprovalRule.end_date > now))
        ).order_by(TransactionApprovalRule.priority.asc()).all()
        
        for rule in rules:
            if rule.applies_to_transaction(amount, category, subcategory):
                return rule
        
        return None
    
    def find_usable_approval(self, account_id: str, amount: float, 
                           category: Optional[str] = None, 
                           subcategory: Optional[str] = None,
                           merchant: Optional[str] = None,
                           transaction_date: Optional[datetime] = None) -> Optional[TransactionApproval]:
        """Find an approval that can be used for this transaction."""
        # Use transaction date if provided, otherwise use current time for approval validity window
        check_date = transaction_date if transaction_date else normalize_for_db_query(get_naive_now())
        
        # Get all approvals for the account and filter manually to avoid timezone comparison issues
        approvals = self.db.query(TransactionApproval).filter(
            TransactionApproval.account_id == account_id,
            TransactionApproval.is_active == True
        ).all()
        
        # Filter by date range using timezone-safe comparison
        valid_approvals = []
        for approval in approvals:
            try:
                # Make all dates timezone-naive for comparison
                start_naive = make_naive(approval.approval_start_date)
                end_naive = make_naive(approval.approval_end_date)
                check_naive = make_naive(check_date)
                
                if start_naive <= check_naive <= end_naive:
                    valid_approvals.append(approval)
            except Exception as e:
                logger.warning(f"Date comparison failed for approval {approval.id}: {str(e)}")
                continue
        
        for approval in valid_approvals:
            if approval.can_approve_transaction(amount, category, subcategory, merchant, transaction_date):
                return approval
        
        return None
    
    def use_approval_for_transaction(self, approval_id: int, transaction_id: str, amount: float) -> bool:
        """Mark an approval as used for a specific transaction."""
        try:
            approval = self.db.query(TransactionApproval).filter(
                TransactionApproval.id == approval_id
            ).first()
            
            if not approval:
                logger.error(f"Approval {approval_id} not found")
                return False
            
            approval.use_for_transaction(transaction_id, amount)
            self.db.commit()
            
            logger.info(f"Approval {approval_id} used for transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to use approval {approval_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def create_approval_request(
        self, restriction_id: int, account_id: str, amount: float, transaction_id: str, 
        description: str, category: Optional[str] = None, 
        subcategory: Optional[str] = None, 
        approval_start_date: datetime = None, 
        approval_end_date: datetime = None
    ) -> TransactionApprovalRequest:
        """Create a new approval request."""
        try:
            # Get the restriction to validate
            restriction = self.db.query(TransactionRestriction).filter(
                TransactionRestriction.id == restriction_id
            ).first()
            
            if not restriction:
                logger.error(f"Restriction {restriction_id} not found")
                return None
            
            # Default dates if not provided
            if approval_start_date is None:
                approval_start_date = get_naive_now()
            if approval_end_date is None:
                approval_end_date = get_naive_now().replace(hour=23, minute=59, second=59)
            
            # Create the request
            request = TransactionApprovalRequest(
                restriction_id=restriction_id,
                requested_by_user_id=requested_by_user_id,
                max_transactions=max_transactions,
                max_amount=max_amount,
                approval_start_date=approval_start_date,
                approval_end_date=approval_end_date,
                category_filter=category_filter,
                subcategory_filter=subcategory_filter,
                request_reason=request_reason
            )
            
            self.db.add(request)
            self.db.commit()
            self.db.refresh(request)
            
            # Send notifications to approvers
            self.send_approval_request_notifications(request)
            
            logger.info(f"Approval request {request.id} created by user {requested_by_user_id}")
            return request
            
        except Exception as e:
            logger.error(f"Failed to create approval request: {str(e)}")
            self.db.rollback()
            return None
    
    def approve_request(self, request_id: int, approved_by_user_id: int, 
                       approval_notes: Optional[str] = None) -> bool:
        """Approve an approval request and create the corresponding approval."""
        try:
            request = self.db.query(TransactionApprovalRequest).filter(
                TransactionApprovalRequest.id == request_id,
                TransactionApprovalRequest.status == 'pending'
            ).first()
            
            if not request:
                logger.error(f"Pending approval request {request_id} not found")
                return False
            
            # Update request status
            request.status = 'approved'
            request.approved_by_user_id = approved_by_user_id
            request.approval_decision_date = get_naive_now()
            request.approval_notes = approval_notes
            
            # Create the approval
            approval = TransactionApproval(
                request_id=request.id,
                account_id=request.restriction.account_id,
                max_transactions=request.max_transactions,
                max_amount=request.max_amount,
                approval_start_date=request.approval_start_date,
                approval_end_date=request.approval_end_date,
                category_filter=request.category_filter,
                subcategory_filter=request.subcategory_filter
            )
            
            self.db.add(approval)
            self.db.commit()
            
            # Send notification to requester
            self.send_approval_decision_notification(request, 'approved')
            
            logger.info(f"Approval request {request_id} approved by user {approved_by_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve request {request_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def deny_request(self, request_id: int, approved_by_user_id: int, 
                    approval_notes: Optional[str] = None) -> bool:
        """Deny an approval request."""
        try:
            request = self.db.query(TransactionApprovalRequest).filter(
                TransactionApprovalRequest.id == request_id,
                TransactionApprovalRequest.status == 'pending'
            ).first()
            
            if not request:
                logger.error(f"Pending approval request {request_id} not found")
                return False
            
            # Update request status
            request.status = 'denied'
            request.approved_by_user_id = approved_by_user_id
            request.approval_decision_date = get_naive_now()
            request.approval_notes = approval_notes
            
            self.db.commit()
            
            # Send notification to requester
            self.send_approval_decision_notification(request, 'denied')
            
            logger.info(f"Approval request {request_id} denied by user {approved_by_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deny request {request_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def send_approval_request_notifications(self, request: TransactionApprovalRequest):
        """Send notifications to approvers about a new approval request."""
        try:
            # Get approver user IDs from the restriction
            approver_ids = request.restriction.get_approver_list()
            
            if not approver_ids:
                logger.warning(f"No approvers found for restriction {request.restriction_id}")
                return
            
            # Get approver user details
            approvers = self.db.query(User).filter(User.id.in_(approver_ids)).all()
            
            if not approvers:
                logger.warning(f"No valid approvers found for IDs: {approver_ids}")
                return
            
            # Get account name
            account = self.db.query(Account).filter(Account.id == request.restriction.account_id).first()
            account_name = account.name if account else "Unknown Account"
            
            # Get requester details
            requester = self.db.query(User).filter(User.id == request.requested_by_user_id).first()
            requester_name = f"{requester.first_name} {requester.last_name}" if requester else "Unknown User"
            
            # Prepare request data for notification
            request_data = {
                'account_name': account_name,
                'requested_by': requester_name,
                'restriction_type': request.restriction.restriction_type,
                'amount_threshold': request.restriction.amount_threshold,
                'category': request.restriction.category,
                'subcategory': request.restriction.subcategory,
                'max_transactions': request.max_transactions,
                'max_amount': request.max_amount,
                'approval_start_date': request.approval_start_date.strftime('%Y-%m-%d %H:%M'),
                'approval_end_date': request.approval_end_date.strftime('%Y-%m-%d %H:%M'),
                'request_reason': request.request_reason
            }
            
            # Create approve/deny URLs (these would be actual web app URLs)
            base_url = "https://your-mercury-app.com"  # This should be configurable
            approve_url = f"{base_url}/approvals/{request.id}/approve"
            deny_url = f"{base_url}/approvals/{request.id}/deny"
            
            # Prepare approver data
            approver_data = []
            for approver in approvers:
                approver_info = {
                    'email': approver.email,
                    'pushover_user_key': getattr(approver.settings, 'pushover_user_key', None) if approver.settings else None
                }
                approver_data.append(approver_info)
            
            # Send notifications
            success = notification_service.send_approval_request_notification(
                approver_data, request_data, approve_url, deny_url
            )
            
            if success:
                logger.info(f"Approval request notifications sent for request {request.id}")
            else:
                logger.warning(f"Failed to send approval request notifications for request {request.id}")
                
        except Exception as e:
            logger.error(f"Failed to send approval request notifications: {str(e)}")
    
    def send_approval_decision_notification(self, request: TransactionApprovalRequest, decision: str):
        """Send notification to requester about approval decision."""
        try:
            # Get requester details
            requester = self.db.query(User).filter(User.id == request.requested_by_user_id).first()
            if not requester:
                logger.warning(f"Requester user {request.requested_by_user_id} not found")
                return
            
            # Get account name
            account = self.db.query(Account).filter(Account.id == request.restriction.account_id).first()
            account_name = account.name if account else "Unknown Account"
            
            # Prepare user data
            user_data = {
                'email': requester.email,
                'pushover_user_key': getattr(requester.settings, 'pushover_user_key', None) if requester.settings else None
            }
            
            # Prepare request data
            request_data = {
                'account_name': account_name,
                'restriction_type': request.restriction.restriction_type,
                'max_transactions': request.max_transactions,
                'max_amount': request.max_amount,
                'approval_start_date': request.approval_start_date.strftime('%Y-%m-%d %H:%M'),
                'approval_end_date': request.approval_end_date.strftime('%Y-%m-%d %H:%M')
            }
            
            # Send notification
            success = notification_service.send_approval_decision_notification(
                user_data, request_data, decision, request.approval_notes
            )
            
            if success:
                logger.info(f"Approval decision notification sent for request {request.id}")
            else:
                logger.warning(f"Failed to send approval decision notification for request {request.id}")
                
        except Exception as e:
            logger.error(f"Failed to send approval decision notification: {str(e)}")
    
    def send_transaction_blocked_notification(self, account_id: str, amount: float, 
                                            description: str, category: Optional[str] = None,
                                            user_id: Optional[int] = None):
        """Send notification when a transaction is blocked due to lack of approval."""
        try:
            # Get account and mercury account details
            account = self.db.query(Account).filter(Account.id == account_id).first()
            if not account:
                logger.warning(f"Account {account_id} not found")
                return
            
            # Get admin users for the mercury account
            mercury_account = account.mercury_account
            if not mercury_account:
                logger.warning(f"Mercury account not found for account {account_id}")
                return
            
            # For now, send to all users with access to this mercury account
            # In a real implementation, you might want to filter by admin role
            admin_users = []
            for user in mercury_account.users:
                if user.is_active:
                    admin_data = {
                        'email': user.email,
                        'username': user.username,
                        'pushover_user_key': getattr(user.settings, 'pushover_user_key', None) if user.settings else None
                    }
                    admin_users.append(admin_data)
            
            # Get user who attempted the transaction
            user_data = {'username': 'Unknown', 'email': 'unknown@example.com'}
            if user_id:
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    user_data = {
                        'username': user.username,
                        'email': user.email,
                        'pushover_user_key': getattr(user.settings, 'pushover_user_key', None) if user.settings else None
                    }
            
            # Prepare transaction data
            transaction_data = {
                'account_name': account.name,
                'amount': amount,
                'description': description,
                'category': category or 'Unknown'
            }
            
            # Send notification
            success = notification_service.send_transaction_blocked_notification(
                admin_users, user_data, transaction_data
            )
            
            if success:
                logger.info(f"Transaction blocked notification sent for account {account_id}")
            else:
                logger.warning(f"Failed to send transaction blocked notification for account {account_id}")
                
        except Exception as e:
            logger.error(f"Failed to send transaction blocked notification: {str(e)}")

    def re_evaluate_all_approvals(self) -> Dict[str, int]:
        """
        Re-evaluate all active approvals and recently expired approvals to ensure they're still valid.
        
        This method should be called during sync to handle cases where:
        1. Transaction categories have been updated
        2. Merchant names (counterparty_name) have changed
        3. Approval criteria need to be re-checked
        4. Usage counts are out of sync with actual logs
        5. Expired approvals need cleanup (checks approvals expired within 5 days)
        
        The 5-day grace period for expired approvals ensures that transaction changes made
        after an approval expires are still properly handled and don't leave orphaned
        approval statuses.
        
        Returns:
            Dict with counts of actions taken:
            - 'approvals_checked': Total approvals evaluated (active + recently expired)
            - 'approvals_deactivated': Approvals that were invalidated
            - 'transaction_logs_removed': Transaction logs that were invalidated
            - 'transactions_reverted': Transactions reverted to violation status
            - 'usage_corrected': Approvals where usage counts were corrected
        """
        logger.info("Starting re-evaluation of all active and recently expired approvals...")
        
        results = {
            'approvals_checked': 0,
            'approvals_deactivated': 0,
            'transaction_logs_removed': 0,
            'transactions_reverted': 0,
            'usage_corrected': 0
        }
        
        try:
            # Get all active approvals AND recently expired approvals (within 5 days)
            # This handles cases where approvals expire but transaction categories are changed afterward
            five_days_ago = get_naive_now() - timedelta(days=5)
            
            approvals_to_check = self.db.query(TransactionApproval).filter(
                or_(
                    TransactionApproval.is_active == True,
                    and_(
                        TransactionApproval.is_active == False,
                        TransactionApproval.approval_end_date >= five_days_ago
                    )
                )
            ).all()
            
            results['approvals_checked'] = len(approvals_to_check)
            
            for approval in approvals_to_check:
                try:
                    approval_invalidated = False
                    logs_to_remove = []
                    valid_transaction_count = 0
                    valid_amount_total = 0.0
                    
                    # Get all transaction logs for this approval to re-validate them
                    transaction_logs = self.db.query(TransactionApprovalLog).filter(
                        TransactionApprovalLog.approval_id == approval.id
                    ).all()
                    
                    logger.info(f"Re-evaluating approval {approval.id} with {len(transaction_logs)} transaction logs")
                    
                    # Re-evaluate each transaction that used this approval
                    for log in transaction_logs:
                        # Get the current transaction data
                        from models.transaction import Transaction
                        transaction = self.db.query(Transaction).filter(
                            Transaction.id == log.transaction_id
                        ).first()
                        
                        if transaction:
                            # Check if this approval would still be valid for this transaction
                            # with current category/merchant data
                            is_still_valid = approval.can_approve_transaction(
                                amount=log.amount,
                                category=transaction.category,
                                subcategory=None,  # Transactions don't currently have subcategory
                                merchant=transaction.counterparty_name,
                                transaction_date=transaction.posted_at
                            )
                            
                            if not is_still_valid:
                                logger.warning(
                                    f"Approval {approval.id} no longer valid for transaction {transaction.id} "
                                    f"due to category/merchant changes. Original: {log.amount}, "
                                    f"Current category: {transaction.category}, "
                                    f"Current merchant: {transaction.counterparty_name}"
                                )
                                
                                # Mark this log for removal
                                logs_to_remove.append(log)
                                
                                # Revert transaction approval status to violation
                                transaction.approval_status = 'violation'
                                transaction.approval_id = None
                                results['transactions_reverted'] += 1
                                
                                approval_invalidated = True
                            else:
                                # This transaction is still valid, count it
                                valid_transaction_count += 1
                                valid_amount_total += abs(log.amount)
                        else:
                            # Transaction doesn't exist anymore, remove the log
                            logger.warning(f"Transaction {log.transaction_id} no longer exists, removing approval log")
                            logs_to_remove.append(log)
                    
                    # Remove invalid logs
                    for log in logs_to_remove:
                        self.db.delete(log)
                        results['transaction_logs_removed'] += 1
                    
                    # Update approval usage counts to match actual valid logs
                    old_used_transactions = approval.used_transactions
                    old_used_amount = approval.used_amount
                    
                    approval.used_transactions = valid_transaction_count
                    approval.used_amount = valid_amount_total
                    
                    if (old_used_transactions != valid_transaction_count or 
                        abs(old_used_amount - valid_amount_total) > 0.01):
                        logger.info(
                            f"Corrected approval {approval.id} usage: "
                            f"transactions {old_used_transactions} -> {valid_transaction_count}, "
                            f"amount {old_used_amount:.2f} -> {valid_amount_total:.2f}"
                        )
                        results['usage_corrected'] += 1
                    
                    # Check if approval should be reactivated after cleanup
                    if approval_invalidated and not approval.is_active:
                        # Check if there's still capacity
                        has_capacity = True
                        if approval.max_transactions is not None and approval.used_transactions >= approval.max_transactions:
                            has_capacity = False
                        if approval.max_amount is not None and approval.used_amount >= approval.max_amount:
                            has_capacity = False
                            
                        if has_capacity:
                            approval.is_active = True
                            logger.info(f"Approval {approval.id} reactivated after removing invalid transactions")
                    
                    # Check if approval should be deactivated due to reaching limits
                    if approval.is_active:
                        should_deactivate = False
                        if approval.max_transactions is not None and approval.used_transactions >= approval.max_transactions:
                            should_deactivate = True
                        if approval.max_amount is not None and approval.used_amount >= approval.max_amount:
                            should_deactivate = True
                            
                        if should_deactivate:
                            approval.is_active = False
                            results['approvals_deactivated'] += 1
                            logger.info(f"Approval {approval.id} deactivated due to reaching limits")
                    
                except Exception as e:
                    logger.error(f"Error re-evaluating approval {approval.id}: {str(e)}")
                    continue
            
            # Commit all changes
            self.db.commit()
            
            logger.info(
                f"Approval re-evaluation completed. "
                f"Checked: {results['approvals_checked']}, "
                f"Deactivated: {results['approvals_deactivated']}, "
                f"Logs removed: {results['transaction_logs_removed']}, "
                f"Transactions reverted: {results['transactions_reverted']}, "
                f"Usage corrected: {results['usage_corrected']}"
            )
            
        except Exception as e:
            logger.error(f"Error during approval re-evaluation: {str(e)}")
            self.db.rollback()
            raise
        
        return results

    def get_approval_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all approvals to identify potential issues.
        
        Returns:
            Dict with health status information:
            - 'total_active_approvals': Number of currently active approvals
            - 'expired_but_active': Approvals that are expired but still marked active
            - 'approvals_with_invalid_requests': Approvals tied to non-approved requests
            - 'fully_used_approvals': Approvals that have reached their limits
            - 'suspicious_transactions': Transactions that may need re-evaluation
        """
        logger.info("Checking approval health status...")
        
        status = {
            'total_active_approvals': 0,
            'expired_but_active': 0,
            'approvals_with_invalid_requests': 0,
            'fully_used_approvals': 0,
            'suspicious_transactions': 0,
            'issues_found': []
        }
        
        try:
            # Get all active approvals
            active_approvals = self.db.query(TransactionApproval).filter(
                TransactionApproval.is_active == True
            ).all()
            
            status['total_active_approvals'] = len(active_approvals)
            now = get_naive_now()
            
            for approval in active_approvals:
                # Check for expired but active approvals
                if naive_datetime_comparison(now, '>', make_naive(approval.approval_end_date)):
                    status['expired_but_active'] += 1
                    status['issues_found'].append(f"Approval {approval.id} is expired but still active")
                
                # Check for approvals with invalid requests
                if approval.request.status != 'approved':
                    status['approvals_with_invalid_requests'] += 1
                    status['issues_found'].append(f"Approval {approval.id} has non-approved request {approval.request.id}")
                
                # Check for fully used approvals that are still active
                transaction_limit_reached = (
                    approval.max_transactions is not None and 
                    approval.used_transactions >= approval.max_transactions
                )
                amount_limit_reached = (
                    approval.max_amount is not None and 
                    approval.used_amount >= approval.max_amount
                )
                
                if transaction_limit_reached or amount_limit_reached:
                    status['fully_used_approvals'] += 1
                    status['issues_found'].append(f"Approval {approval.id} has reached its limits but is still active")
                
                # Check for suspicious transaction patterns
                transaction_logs = self.db.query(TransactionApprovalLog).filter(
                    TransactionApprovalLog.approval_id == approval.id
                ).all()
                
                for log in transaction_logs:
                    from models.transaction import Transaction
                    transaction = self.db.query(Transaction).filter(
                        Transaction.id == log.transaction_id
                    ).first()
                    
                    if transaction:
                        # Quick check if approval would still be valid
                        is_still_valid = approval.can_approve_transaction(
                            amount=log.amount,
                            category=transaction.category,
                            subcategory=None,  # Transactions don't currently have subcategory
                            merchant=transaction.counterparty_name,
                            transaction_date=transaction.posted_at
                        )
                        
                        if not is_still_valid:
                            status['suspicious_transactions'] += 1
                            status['issues_found'].append(
                                f"Transaction {transaction.id} may no longer be valid for approval {approval.id}"
                            )
            
            logger.info(f"Approval health check completed. Found {len(status['issues_found'])} potential issues")
            
        except Exception as e:
            logger.error(f"Error during approval health check: {str(e)}")
            status['error'] = str(e)
            
        return status


def get_approval_manager(db_session: Session) -> TransactionApprovalManager:
    """Get a transaction approval manager instance."""
    return TransactionApprovalManager(db_session)
