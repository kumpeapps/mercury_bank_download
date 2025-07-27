"""Transaction approval logic for checking and processing approvals."""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class TransactionApprovalManager:
    """Manages transaction approval logic and workflow."""
    
    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
    
    def check_transaction_approval_status(self, account_id: str, amount: float, 
                                        category: Optional[str] = None, 
                                        subcategory: Optional[str] = None) -> Tuple[str, Optional[int]]:
        """
        Check if a transaction requires approval and its current status.
        
        Args:
            account_id: Account ID for the transaction
            amount: Transaction amount
            category: Transaction category (optional)
            subcategory: Transaction subcategory (optional)
            
        Returns:
            Tuple of (status, approval_id) where status is one of:
            - 'not_required': No approval needed
            - 'auto_approved': Automatically approved by rule
            - 'approved': Has valid approval
            - 'pending': Requires approval but none available
            And approval_id is the ID of the approval used (if any)
        """
        # First check if there are any active restrictions for this account
        restrictions = self.get_active_restrictions(account_id)
        
        if not restrictions:
            return 'not_required', None
        
        # Check if any restrictions apply to this transaction
        applicable_restrictions = []
        for restriction in restrictions:
            if restriction.applies_to_transaction(amount, category, subcategory):
                applicable_restrictions.append(restriction)
        
        if not applicable_restrictions:
            return 'not_required', None
        
        # Check for auto-approval rules (processed in priority order)
        auto_approval_rule = self.check_auto_approval_rules(account_id, amount, category, subcategory)
        if auto_approval_rule:
            logger.info(f"Transaction auto-approved by rule: {auto_approval_rule.rule_name}")
            return 'auto_approved', None
        
        # Check for existing approvals that can cover this transaction
        approval = self.find_usable_approval(account_id, amount, category, subcategory)
        if approval:
            return 'approved', approval.id
        
        # No approval available - transaction requires approval
        return 'pending', None
    
    def get_active_restrictions(self, account_id: str) -> List[TransactionRestriction]:
        """Get all active restrictions for an account."""
        now = datetime.utcnow()
        return self.db.query(TransactionRestriction).filter(
            TransactionRestriction.account_id == account_id,
            TransactionRestriction.is_active == True,
            TransactionRestriction.start_date <= now,
            (TransactionRestriction.end_date.is_(None) | (TransactionRestriction.end_date > now))
        ).all()
    
    def check_auto_approval_rules(self, account_id: str, amount: float, 
                                category: Optional[str] = None, 
                                subcategory: Optional[str] = None) -> Optional[TransactionApprovalRule]:
        """Check if any auto-approval rules apply to this transaction."""
        now = datetime.utcnow()
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
                           transaction_date: datetime = None) -> Optional[TransactionApproval]:
        """Find an approval that can be used for this transaction."""
        # Use transaction date if provided, otherwise use current time for approval validity window
        check_date = transaction_date if transaction_date else datetime.utcnow()
        
        approvals = self.db.query(TransactionApproval).filter(
            TransactionApproval.account_id == account_id,
            TransactionApproval.is_active == True,
            TransactionApproval.approval_start_date <= check_date,
            TransactionApproval.approval_end_date > check_date
        ).all()
        
        for approval in approvals:
            if approval.can_approve_transaction(amount, category, subcategory, transaction_date):
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
    
    def create_approval_request(self, restriction_id: int, requested_by_user_id: int,
                              max_transactions: Optional[int] = None,
                              max_amount: Optional[float] = None,
                              approval_start_date: datetime = None,
                              approval_end_date: datetime = None,
                              category_filter: Optional[str] = None,
                              subcategory_filter: Optional[str] = None,
                              request_reason: Optional[str] = None) -> Optional[TransactionApprovalRequest]:
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
                approval_start_date = datetime.utcnow()
            if approval_end_date is None:
                approval_end_date = datetime.utcnow().replace(hour=23, minute=59, second=59)
            
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
            request.approval_decision_date = datetime.utcnow()
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
            request.approval_decision_date = datetime.utcnow()
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


def get_approval_manager(db_session: Session) -> TransactionApprovalManager:
    """Get a transaction approval manager instance."""
    return TransactionApprovalManager(db_session)
