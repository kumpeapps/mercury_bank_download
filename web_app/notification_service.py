"""Notification service for sending emails and Pushover notifications."""

import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
import logging
from simple_timezone_fix import get_naive_now

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending email and Pushover notifications."""
    
    def __init__(self, db_session=None):
        """Initialize notification service with configuration from database or environment."""
        self.db_session = db_session
        
        if db_session:
            # Load configuration from database SystemSetting
            self._load_config_from_db()
        else:
            # Fallback to environment variables
            self._load_config_from_env()
    
    def _load_config_from_db(self):
        """Load configuration from database SystemSetting."""
        from models.system_setting import SystemSetting
        
        # Email configuration from database
        self.smtp_server = SystemSetting.get_value(self.db_session, 'smtp_server')
        self.smtp_port = int(SystemSetting.get_value(self.db_session, 'smtp_port', '587'))
        self.smtp_username = SystemSetting.get_value(self.db_session, 'smtp_username')
        self.smtp_password = SystemSetting.get_value(self.db_session, 'smtp_password')
        self.smtp_from_email = SystemSetting.get_value(self.db_session, 'smtp_from_email')
        self.smtp_use_tls = SystemSetting.get_bool_value(self.db_session, 'smtp_use_tls', True)
        
        # Pushover configuration from database
        self.pushover_token = SystemSetting.get_value(self.db_session, 'pushover_app_token')
        self.pushover_enabled = SystemSetting.get_bool_value(self.db_session, 'approval_pushover_enabled', False) and bool(self.pushover_token)
        
        logger.info(f"Pushover config: token={'***' if self.pushover_token else 'None'}, enabled={self.pushover_enabled}")
        
        # Email enabled if SMTP is configured
        self.email_enabled = bool(
            self.smtp_server and 
            self.smtp_username and 
            self.smtp_password and 
            self.smtp_from_email
        )
    
    def _load_config_from_env(self):
        """Load configuration from environment variables (fallback)."""
        # Email configuration from environment
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_from_email = os.getenv('SMTP_FROM_EMAIL')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # Pushover configuration
        self.pushover_token = os.getenv('PUSHOVER_TOKEN')
        self.pushover_enabled = bool(self.pushover_token)
        
        # Email enabled if SMTP is configured
        self.email_enabled = bool(
            self.smtp_server and 
            self.smtp_username and 
            self.smtp_password and 
            self.smtp_from_email
        )
    
    def send_email(self, to_email: str, subject: str, message: str) -> bool:
        """
        Send an email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            message: Email message body
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.email_enabled:
            logger.warning("Email not configured, skipping email notification")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(message, 'html'))
            
            # Create SMTP session
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(self.smtp_from_email, to_email, text)
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_pushover(self, user_key: str, subject: str, message: str, 
                     url: Optional[str] = None, priority: int = 0) -> bool:
        """
        Send a Pushover notification.
        
        Args:
            user_key: Pushover user key
            subject: Notification title
            message: Notification message
            url: Optional URL to include
            priority: Priority level (-2 to 2)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.pushover_enabled:
            logger.warning("Pushover not configured, skipping Pushover notification")
            return False
        
        try:
            data = {
                'token': self.pushover_token,
                'user': user_key,
                'title': subject,
                'message': message,
                'priority': priority,
                'html': '1'  # Enable HTML formatting
            }
            
            if url:
                data['url'] = url
                data['url_title'] = 'View Details'
            
            response = requests.post(
                'https://api.pushover.net/1/messages.json',
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Pushover notification sent successfully to {user_key}")
                return True
            else:
                logger.error(f"Pushover API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Pushover notification to {user_key}: {str(e)}")
            return False
    
    def send_pushover_with_actions(self, user_key: str, subject: str, message: str, 
                                  url: Optional[str] = None, url_title: str = 'View Details',
                                  actions: Optional[list] = None, priority: int = 0) -> bool:
        """
        Send a Pushover notification with action buttons.
        
        Args:
            user_key: Pushover user key
            subject: Notification title
            message: Notification message (HTML supported)
            url: Optional URL to include
            url_title: Title for the URL button
            actions: List of action dictionaries with 'action', 'title', 'url', 'url_title'
            priority: Priority level (-2 to 2)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.pushover_enabled:
            logger.warning("Pushover not configured, skipping Pushover notification")
            return False
        
        try:
            data = {
                'token': self.pushover_token,
                'user': user_key,
                'title': subject,
                'message': message,
                'priority': priority,
                'html': '1'  # Enable HTML formatting
            }
            
            if url:
                data['url'] = url
                data['url_title'] = url_title
            
            # Add action buttons if provided
            if actions:
                for i, action in enumerate(actions[:3]):  # Pushover supports up to 3 action buttons
                    data[f'actions[{i}][action]'] = action.get('action', f'action_{i}')
                    data[f'actions[{i}][title]'] = action.get('title', f'Action {i+1}')
                    if action.get('url'):
                        data[f'actions[{i}][url]'] = action['url']
                        data[f'actions[{i}][url_title]'] = action.get('url_title', action.get('title', f'Action {i+1}'))
            
            response = requests.post(
                'https://api.pushover.net/1/messages.json',
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Pushover notification with actions sent successfully to {user_key}")
                return True
            else:
                logger.error(f"Pushover API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Pushover notification with actions to {user_key}: {str(e)}")
            return False
    
    def send_approval_request_notification(self, approvers: list, request_data: Dict[str, Any], 
                                         approve_url: str, deny_url: str) -> bool:
        """
        Send approval request notifications to all approvers.
        
        Args:
            approvers: List of approver user dictionaries with email/pushover info
            request_data: Dictionary with request details
            approve_url: URL to approve the request
            deny_url: URL to deny the request
            
        Returns:
            bool: True if at least one notification was sent successfully
        """
        subject = f"Transaction Approval Request - {request_data.get('mercury_account_name', request_data.get('account_name', 'Unknown Account'))}"
        
        # Create details URL (remove the /approve or /deny from the approve_url)
        details_url = approve_url.replace('/approve', '/details')
        
        # Create HTML email content
        html_message = f"""
        <h2>Transaction Approval Request</h2>
        
        <p><strong>Mercury Account:</strong> {request_data.get('mercury_account_name', 'Unknown')}</p>
        <p><strong>Specific Accounts:</strong> {request_data.get('account_name', 'Unknown')}</p>
        <p><strong>Requested by:</strong> {request_data.get('requested_by', 'Unknown')}</p>
        <p><strong>Request Type:</strong> {request_data.get('restriction_type', 'Unknown')}</p>
        
        {f"<p><strong>Amount Threshold:</strong> ${request_data['amount_threshold']:,.2f}</p>" if request_data.get('amount_threshold') else ""}
        {f"<p><strong>Category:</strong> {request_data['category']}</p>" if request_data.get('category') else ""}
        {f"<p><strong>Subcategory:</strong> {request_data['subcategory']}</p>" if request_data.get('subcategory') else ""}
        
        <p><strong>Max Transactions:</strong> {request_data.get('max_transactions', 'Unlimited')}</p>
        <p><strong>Max Amount:</strong> ${request_data.get('max_amount', 'Unlimited')}</p>
        <p><strong>Valid From:</strong> {request_data.get('approval_start_date', 'Unknown')}</p>
        <p><strong>Valid Until:</strong> {request_data.get('approval_end_date', 'Unknown')}</p>
        
        {f"<p><strong>Reason:</strong> {request_data['request_reason']}</p>" if request_data.get('request_reason') else ""}
        
        <div style="margin: 20px 0;">
            <a href="{approve_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">Approve</a>
            <a href="{deny_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Deny</a>
        </div>
        
        <p><em>This request was submitted on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        """
        
        # Create text message for Pushover (with HTML for action buttons)
        pushover_message = f"""<b>Transaction Approval Request</b>
        
<b>Mercury Account:</b> {request_data.get('mercury_account_name', 'Unknown')}
<b>Specific Accounts:</b> {request_data.get('account_name', 'Unknown')}
<b>Requested by:</b> {request_data.get('requested_by', 'Unknown')}
<b>Type:</b> {request_data.get('restriction_type', 'Unknown')}
<b>Max Amount:</b> ${request_data.get('max_amount', 'Unlimited')}
<b>Valid:</b> {request_data.get('approval_start_date', 'Unknown')} to {request_data.get('approval_end_date', 'Unknown')}

{f"<b>Reason:</b> {request_data['request_reason']}" if request_data.get('request_reason') else ""}"""
        
        success_count = 0
        
        for approver in approvers:
            logger.info(f"Processing approver: email={approver.get('email')}, pushover_key={'***' if approver.get('pushover_user_key') else 'None'}")
            
            # Send email if email address is available
            if approver.get('email'):
                if self.send_email(approver['email'], subject, html_message):
                    success_count += 1
            
            # Send Pushover with action buttons if user key is available
            if approver.get('pushover_user_key'):
                logger.info(f"Attempting Pushover notification to {approver.get('pushover_user_key')[:10]}...")
                if self.send_pushover_with_actions(
                    approver['pushover_user_key'], 
                    subject, 
                    pushover_message,
                    url=details_url,
                    url_title='View Details',
                    actions=[
                        {'action': 'approve', 'title': 'Approve', 'url': approve_url, 'url_title': 'Approve Request'},
                        {'action': 'deny', 'title': 'Deny', 'url': deny_url, 'url_title': 'Deny Request'}
                    ],
                    priority=1  # High priority for approval requests
                ):
                    success_count += 1
            else:
                logger.info("No Pushover user key found for approver")
        
        return success_count > 0
    
    def send_approval_decision_notification(self, user_data: Dict[str, Any], 
                                          request_data: Dict[str, Any], 
                                          decision: str, notes: Optional[str] = None) -> bool:
        """
        Send notification about approval decision to the requesting user.
        
        Args:
            user_data: Dictionary with user email/pushover info
            request_data: Dictionary with request details
            decision: 'approved' or 'denied'
            notes: Optional notes from approver
            
        Returns:
            bool: True if notification was sent successfully
        """
        subject = f"Transaction Approval {decision.title()} - {request_data.get('account_name', 'Unknown Account')}"
        
        status_color = "#28a745" if decision == "approved" else "#dc3545"
        status_text = "APPROVED" if decision == "approved" else "DENIED"
        
        # Create HTML email content
        html_message = f"""
        <h2 style="color: {status_color};">Transaction Approval {status_text}</h2>
        
        <p>Your transaction approval request has been <strong style="color: {status_color};">{decision}</strong>.</p>
        
        <h3>Request Details:</h3>
        <p><strong>Account:</strong> {request_data.get('account_name', 'Unknown')}</p>
        <p><strong>Request Type:</strong> {request_data.get('restriction_type', 'Unknown')}</p>
        <p><strong>Max Transactions:</strong> {request_data.get('max_transactions', 'Unlimited')}</p>
        <p><strong>Max Amount:</strong> ${request_data.get('max_amount', 'Unlimited')}</p>
        <p><strong>Valid Period:</strong> {request_data.get('approval_start_date', 'Unknown')} to {request_data.get('approval_end_date', 'Unknown')}</p>
        
        {f"<h3>Approver Notes:</h3><p>{notes}</p>" if notes else ""}
        
        <p><em>Decision made on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        """
        
        # Create text message for Pushover
        text_message = f"""Transaction Approval {status_text}
        
Your request for {request_data.get('account_name', 'Unknown')} has been {decision}.

Max Amount: ${request_data.get('max_amount', 'Unlimited')}
{f"Notes: {notes}" if notes else ""}"""
        
        success = False
        
        # Send email if available
        if user_data.get('email'):
            if self.send_email(user_data['email'], subject, html_message):
                success = True
        
        # Send Pushover if available
        if user_data.get('pushover_user_key'):
            priority = 1 if decision == "approved" else 0
            if self.send_pushover(
                user_data['pushover_user_key'], 
                subject, 
                text_message,
                priority=priority
            ):
                success = True
        
        return success
    
    def send_transaction_blocked_notification(self, admin_users: list, user_data: Dict[str, Any],
                                           transaction_data: Dict[str, Any]) -> bool:
        """
        Send notification when a transaction is blocked due to lack of approval.
        
        Args:
            admin_users: List of admin user dictionaries
            user_data: Dictionary with user who attempted the transaction
            transaction_data: Dictionary with transaction details
            
        Returns:
            bool: True if at least one notification was sent successfully
        """
        subject = f"Transaction Blocked - Approval Required"
        
        # Create HTML email content for admins
        html_message = f"""
        <h2 style="color: #dc3545;">Transaction Blocked - Approval Required</h2>
        
        <p>A transaction has been blocked because it requires approval but no valid approval was found.</p>
        
        <h3>Transaction Details:</h3>
        <p><strong>Account:</strong> {transaction_data.get('account_name', 'Unknown')}</p>
        <p><strong>Amount:</strong> ${transaction_data.get('amount', 0):,.2f}</p>
        <p><strong>Description:</strong> {transaction_data.get('description', 'Unknown')}</p>
        <p><strong>Category:</strong> {transaction_data.get('category', 'Unknown')}</p>
        <p><strong>User:</strong> {user_data.get('username', 'Unknown')} ({user_data.get('email', 'Unknown')})</p>
        
        <p><strong>Date:</strong> {get_naive_now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <p>Please review the approval restrictions for this account and create appropriate approvals if needed.</p>
        """
        
        # Create text message for Pushover
        text_message = f"""Transaction Blocked
        
A ${transaction_data.get('amount', 0):,.2f} transaction on {transaction_data.get('account_name', 'Unknown')} was blocked due to approval requirements.

User: {user_data.get('username', 'Unknown')}
Description: {transaction_data.get('description', 'Unknown')}"""
        
        success_count = 0
        
        # Also notify the user who attempted the transaction
        all_recipients = admin_users + [user_data]
        
        for recipient in all_recipients:
            # Send email if available
            if recipient.get('email'):
                if self.send_email(recipient['email'], subject, html_message):
                    success_count += 1
            
            # Send Pushover if available
            if recipient.get('pushover_user_key'):
                if self.send_pushover(
                    recipient['pushover_user_key'], 
                    subject, 
                    text_message,
                    priority=1  # High priority for blocked transactions
                ):
                    success_count += 1
        
        return success_count > 0


# Global notification service instance
notification_service = NotificationService()
