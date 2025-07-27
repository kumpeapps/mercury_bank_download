"""Flask routes for transaction approval management."""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, g
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.transaction_approval import (
    TransactionRestriction,
    TransactionApprovalRequest,
    TransactionApproval,
    TransactionApprovalRule
)
from models.account import Account
from models.user import User
from models.mercury_account import MercuryAccount
from database_config import Session
from functools import wraps
import json
import logging

logger = logging.getLogger(__name__)


def admin_required(f):
    """Decorator to require admin access for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        
        user = User.query.get(current_user.id)
        if (
            not user
            or not user.is_active
            or (not user.has_role("admin") and not user.has_role("super-admin"))
        ):
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("dashboard"))
        
        return f(*args, **kwargs)
    return decorated_function

approval_bp = Blueprint('approval', __name__)


@approval_bp.route('/restrictions')
@login_required
@admin_required
def list_restrictions():
    """List all transaction restrictions."""
    page = request.args.get('page', 1, type=int)
    
    # Get accounts user has access to
    if current_user.is_super_admin:
        restrictions = TransactionRestriction.query.paginate(
            page=page, per_page=20, error_out=False
        )
    else:
        # Filter by accounts user has access to
        account_ids = [acc.id for acc in current_user.accounts]
        restrictions = TransactionRestriction.query.filter(
            TransactionRestriction.account_id.in_(account_ids)
        ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('approval/restrictions.html', restrictions=restrictions)


@approval_bp.route('/restrictions/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_restriction():
    """Create a new transaction restriction."""
    if request.method == 'POST':
        try:
            # Parse form data
            account_id = request.form.get('account_id')
            restriction_type = request.form.get('restriction_type')
            amount_threshold = request.form.get('amount_threshold')
            category = request.form.get('category')
            subcategory = request.form.get('subcategory')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            approvers = request.form.getlist('approvers')
            
            # Validate required fields
            if not account_id or not restriction_type or not start_date:
                flash('Account, restriction type, and start date are required.', 'error')
                return render_template('approval/create_restriction.html', 
                                     accounts=get_user_accounts(),
                                     users=get_approver_users())
            
            # Parse dates
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
            
            # Parse amount threshold
            amount_threshold = float(amount_threshold) if amount_threshold else None
            
            # Create restriction
            restriction = TransactionRestriction(
                account_id=account_id,
                restriction_type=restriction_type,
                amount_threshold=amount_threshold,
                category=category if category else None,
                subcategory=subcategory if subcategory else None,
                start_date=start_date,
                end_date=end_date,
                approver_user_ids=json.dumps(approvers) if approvers else None,
                created_by_user_id=current_user.id
            )
            
            db.session.add(restriction)
            db.session.commit()
            
            flash('Transaction restriction created successfully.', 'success')
            return redirect(url_for('approval.list_restrictions'))
            
        except ValueError as e:
            flash('Invalid date or amount format.', 'error')
        except Exception as e:
            flash(f'Error creating restriction: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('approval/create_restriction.html', 
                         accounts=get_user_accounts(),
                         users=get_approver_users())


@approval_bp.route('/restrictions/<int:restriction_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_restriction(restriction_id):
    """Edit an existing transaction restriction."""
    restriction = TransactionRestriction.query.get_or_404(restriction_id)
    
    # Check if user has access to this restriction's account
    if not current_user.is_super_admin and restriction.account_id not in [acc.id for acc in current_user.accounts]:
        flash('You do not have permission to edit this restriction.', 'error')
        return redirect(url_for('approval.list_restrictions'))
    
    if request.method == 'POST':
        try:
            # Update restriction fields
            restriction.restriction_type = request.form.get('restriction_type')
            restriction.amount_threshold = float(request.form.get('amount_threshold')) if request.form.get('amount_threshold') else None
            restriction.category = request.form.get('category') if request.form.get('category') else None
            restriction.subcategory = request.form.get('subcategory') if request.form.get('subcategory') else None
            restriction.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            restriction.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None
            
            approvers = request.form.getlist('approvers')
            restriction.approver_user_ids = json.dumps(approvers) if approvers else None
            
            restriction.is_active = 'is_active' in request.form
            
            db.session.commit()
            flash('Restriction updated successfully.', 'success')
            return redirect(url_for('approval.list_restrictions'))
            
        except ValueError:
            flash('Invalid date or amount format.', 'error')
        except Exception as e:
            flash(f'Error updating restriction: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('approval/edit_restriction.html', 
                         restriction=restriction,
                         accounts=get_user_accounts(),
                         users=get_approver_users())


@approval_bp.route('/restrictions/<int:restriction_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_restriction(restriction_id):
    """Delete a transaction restriction."""
    restriction = TransactionRestriction.query.get_or_404(restriction_id)
    
    # Check if user has access to this restriction's account
    if not current_user.is_super_admin and restriction.account_id not in [acc.id for acc in current_user.accounts]:
        flash('You do not have permission to delete this restriction.', 'error')
        return redirect(url_for('approval.list_restrictions'))
    
    try:
        db.session.delete(restriction)
        db.session.commit()
        flash('Restriction deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting restriction: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('approval.list_restrictions'))


@approval_bp.route('/requests')
@login_required
def list_approval_requests():
    """List approval requests (pending, approved, denied)."""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    # Base query
    query = TransactionApprovalRequest.query
    
    # Filter by status if specified
    if status_filter != 'all':
        query = query.filter(TransactionApprovalRequest.status == status_filter)
    
    # Filter by user permissions
    if not current_user.is_super_admin:
        # Show requests for accounts user has access to or requests they made
        account_ids = [acc.id for acc in current_user.accounts]
        query = query.join(TransactionRestriction).filter(
            (TransactionRestriction.account_id.in_(account_ids)) |
            (TransactionApprovalRequest.requested_by_user_id == current_user.id)
        )
    
    requests = query.order_by(TransactionApprovalRequest.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('approval/requests.html', requests=requests, status_filter=status_filter)


@approval_bp.route('/requests/<int:request_id>/details')
@login_required
def get_approval_request_details(request_id):
    """Get detailed information about a specific approval request."""
    try:
        db_session = Session()
        
        # Get the request
        approval_request = db_session.query(TransactionApprovalRequest).filter_by(id=request_id).first()
        
        if not approval_request:
            return jsonify({'error': 'Request not found'}), 404
        
        # Check permissions
        if not current_user.is_super_admin:
            # User can view if they made the request or have access to the account
            account_ids = [acc.id for acc in current_user.accounts]
            if (approval_request.requested_by_user_id != current_user.id and 
                approval_request.restriction.account_id not in account_ids):
                return jsonify({'error': 'Access denied'}), 403
        
        # Build response data
        response_data = {
            'request': {
                'id': approval_request.id,
                'account_name': approval_request.restriction.account.name if approval_request.restriction.account else 'Unknown',
                'requested_by_name': f"{approval_request.requested_by.first_name} {approval_request.requested_by.last_name}",
                'created_at': approval_request.created_at.strftime('%Y-%m-%d %H:%M:%S') if approval_request.created_at else '',
                'status': approval_request.status,
                'max_amount': approval_request.max_amount,
                'max_transactions': approval_request.max_transactions,
                'approval_start_date': approval_request.approval_start_date.strftime('%Y-%m-%d') if approval_request.approval_start_date else '',
                'approval_end_date': approval_request.approval_end_date.strftime('%Y-%m-%d') if approval_request.approval_end_date else '',
                'category_filter': approval_request.category_filter,
                'subcategory_filter': approval_request.subcategory_filter,
                'request_reason': approval_request.request_reason,
                'approval_notes': approval_request.approval_notes,
                'approved_by_name': f"{approval_request.approved_by.first_name} {approval_request.approved_by.last_name}" if approval_request.approved_by else None,
                'approval_decision_date': approval_request.approval_decision_date.strftime('%Y-%m-%d %H:%M:%S') if approval_request.approval_decision_date else None
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'Error loading request details: {str(e)}'}), 500
    finally:
        db_session.close()


@approval_bp.route('/requests/new', methods=['GET', 'POST'])
@login_required
def create_approval_request():
    """Create a new approval request."""
    if request.method == 'POST':
        try:
            restriction_id = request.form.get('restriction_id')
            max_transactions = request.form.get('max_transactions')
            max_amount = request.form.get('max_amount')
            approval_start_date = request.form.get('approval_start_date')
            approval_end_date = request.form.get('approval_end_date')
            category_filter = request.form.get('category_filter')
            subcategory_filter = request.form.get('subcategory_filter')
            request_reason = request.form.get('request_reason')
            
            # Validate required fields
            if not restriction_id or not approval_start_date or not approval_end_date:
                flash('Restriction, start date, and end date are required.', 'error')
                return render_template('approval/create_request.html', 
                                     restrictions=get_user_restrictions())
            
            # Parse dates
            approval_start_date = datetime.strptime(approval_start_date, '%Y-%m-%d')
            approval_end_date = datetime.strptime(approval_end_date, '%Y-%m-%d')
            
            # Parse numeric fields
            max_transactions = int(max_transactions) if max_transactions else None
            max_amount = float(max_amount) if max_amount else None
            
            # Create approval request
            db_session = Session()
            try:
                approval_request = TransactionApprovalRequest(
                    restriction_id=int(restriction_id),
                    requested_by_user_id=current_user.id,
                    max_transactions=max_transactions,
                    max_amount=max_amount,
                    approval_start_date=approval_start_date,
                    approval_end_date=approval_end_date,
                    category_filter=category_filter if category_filter else None,
                    subcategory_filter=subcategory_filter if subcategory_filter else None,
                    request_reason=request_reason
                )
                
                db_session.add(approval_request)
                db_session.commit()
                
                # Send notification to approvers
                try:
                    from sync_app.transaction_approval_manager import TransactionApprovalManager
                    approval_manager = TransactionApprovalManager(db_session)
                    approval_manager.send_approval_request_notifications(approval_request)
                except Exception as notify_error:
                    logger.warning(f"Failed to send approval request notifications: {str(notify_error)}")
                
                flash('Approval request submitted successfully.', 'success')
                return redirect(url_for('approval.list_approval_requests'))
            finally:
                db_session.close()
            
        except ValueError:
            flash('Invalid date or number format.', 'error')
        except Exception as e:
            flash(f'Error creating approval request: {str(e)}', 'error')
    
    return render_template('approval/create_request.html', 
                         restrictions=get_user_restrictions())


@approval_bp.route('/requests/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_request(request_id):
    """Approve an approval request."""
    approval_request = TransactionApprovalRequest.query.get_or_404(request_id)
    
    # Check if user is authorized to approve this request
    if not can_approve_request(approval_request, current_user):
        flash('You are not authorized to approve this request.', 'error')
        return redirect(url_for('approval.list_approval_requests'))
    
    if approval_request.status != 'pending':
        flash('This request has already been processed.', 'error')
        return redirect(url_for('approval.list_approval_requests'))
    
    try:
        approval_notes = request.form.get('approval_notes', '')
        
        # Update request
        approval_request.status = 'approved'
        approval_request.approved_by_user_id = current_user.id
        approval_request.approval_decision_date = datetime.utcnow()
        approval_request.approval_notes = approval_notes
        
        # Create the approval
        approval = TransactionApproval(
            request_id=approval_request.id,
            account_id=approval_request.restriction.account_id,
            max_transactions=approval_request.max_transactions,
            max_amount=approval_request.max_amount,
            approval_start_date=approval_request.approval_start_date,
            approval_end_date=approval_request.approval_end_date,
            category_filter=approval_request.category_filter,
            subcategory_filter=approval_request.subcategory_filter
        )
        
        db.session.add(approval)
        db.session.commit()
        
        # TODO: Send notification to requester
        
        flash('Approval request approved successfully.', 'success')
        
    except Exception as e:
        flash(f'Error approving request: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('approval.list_approval_requests'))


@approval_bp.route('/requests/<int:request_id>/deny', methods=['POST'])
@login_required
def deny_request(request_id):
    """Deny an approval request."""
    approval_request = TransactionApprovalRequest.query.get_or_404(request_id)
    
    # Check if user is authorized to approve this request
    if not can_approve_request(approval_request, current_user):
        flash('You are not authorized to deny this request.', 'error')
        return redirect(url_for('approval.list_approval_requests'))
    
    if approval_request.status != 'pending':
        flash('This request has already been processed.', 'error')
        return redirect(url_for('approval.list_approval_requests'))
    
    try:
        approval_notes = request.form.get('approval_notes', '')
        
        # Update request
        approval_request.status = 'denied'
        approval_request.approved_by_user_id = current_user.id
        approval_request.approval_decision_date = datetime.utcnow()
        approval_request.approval_notes = approval_notes
        
        db.session.commit()
        
        # TODO: Send notification to requester
        
        flash('Approval request denied.', 'success')
        
    except Exception as e:
        flash(f'Error denying request: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('approval.list_approval_requests'))


@approval_bp.route('/rules')
@login_required
@admin_required
def list_approval_rules():
    """List auto-approval rules."""
    page = request.args.get('page', 1, type=int)
    
    # Get rules user has access to
    if current_user.is_super_admin:
        rules = TransactionApprovalRule.query.order_by(
            TransactionApprovalRule.priority.asc()
        ).paginate(page=page, per_page=20, error_out=False)
    else:
        # Filter by accounts user has access to
        account_ids = [acc.id for acc in current_user.accounts]
        rules = TransactionApprovalRule.query.filter(
            TransactionApprovalRule.account_id.in_(account_ids)
        ).order_by(TransactionApprovalRule.priority.asc()).paginate(
            page=page, per_page=20, error_out=False
        )
    
    return render_template('approval/rules.html', rules=rules)


@approval_bp.route('/rules/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_approval_rule():
    """Create a new auto-approval rule."""
    if request.method == 'POST':
        try:
            # Parse form data
            account_id = request.form.get('account_id')
            rule_name = request.form.get('rule_name')
            rule_type = request.form.get('rule_type')
            amount_threshold = request.form.get('amount_threshold')
            category = request.form.get('category')
            subcategory = request.form.get('subcategory')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            priority = request.form.get('priority')
            
            # Validate required fields
            if not account_id or not rule_name or not rule_type or not start_date or not priority:
                flash('Account, rule name, rule type, start date, and priority are required.', 'error')
                return render_template('approval/create_rule.html', 
                                     accounts=get_user_accounts())
            
            # Parse dates
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
            
            # Parse amount threshold and priority
            amount_threshold = float(amount_threshold) if amount_threshold else None
            priority = int(priority)
            
            # Create rule
            rule = TransactionApprovalRule(
                account_id=account_id,
                rule_name=rule_name,
                rule_type=rule_type,
                amount_threshold=amount_threshold,
                category=category if category else None,
                subcategory=subcategory if subcategory else None,
                start_date=start_date,
                end_date=end_date,
                priority=priority,
                created_by_user_id=current_user.id
            )
            
            db.session.add(rule)
            db.session.commit()
            
            flash('Auto-approval rule created successfully.', 'success')
            return redirect(url_for('approval.list_approval_rules'))
            
        except ValueError:
            flash('Invalid date, amount, or priority format.', 'error')
        except Exception as e:
            flash(f'Error creating rule: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('approval/create_rule.html', 
                         accounts=get_user_accounts())


def get_user_accounts():
    """Get accounts the current user has access to."""
    if current_user.is_super_admin:
        return Account.query.all()
    else:
        return current_user.accounts


def get_approver_users():
    """Get users who can be approvers."""
    return User.query.filter(User.is_active == True).all()


def get_user_restrictions():
    """Get restrictions for accounts the user has access to."""
    if current_user.is_super_admin:
        return TransactionRestriction.query.filter(
            TransactionRestriction.is_active == True
        ).all()
    else:
        account_ids = [acc.id for acc in current_user.accounts]
        return TransactionRestriction.query.filter(
            TransactionRestriction.account_id.in_(account_ids),
            TransactionRestriction.is_active == True
        ).all()


def can_approve_request(approval_request, user):
    """Check if a user can approve a specific request."""
    if user.is_super_admin:
        return True
    
    # Check if user is in the restriction's approver list
    approver_ids = approval_request.restriction.get_approver_list()
    return user.id in approver_ids


@approval_bp.route('/re-evaluate-approvals', methods=['POST'])
@login_required
@admin_required
def re_evaluate_approvals():
    """Manually trigger re-evaluation of all approvals."""
    try:
        # Import the sync app's approval manager
        import sys
        import os
        sync_app_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sync_app')
        sys.path.insert(0, sync_app_path)
        
        try:
            from transaction_approval_manager import get_approval_manager
            
            db = Session()
            try:
                approval_manager = get_approval_manager(db)
                results = approval_manager.re_evaluate_all_approvals()
                
                flash(
                    f"Approval re-evaluation completed successfully! "
                    f"Checked: {results['approvals_checked']}, "
                    f"Deactivated: {results['approvals_deactivated']}, "
                    f"Logs removed: {results['transaction_logs_removed']}, "
                    f"Transactions reverted: {results['transactions_reverted']}",
                    "success"
                )
                
                logger.info(
                    f"Manual approval re-evaluation triggered by user {current_user.id}. "
                    f"Results: {results}"
                )
                
            finally:
                db.close()
                
        finally:
            # Remove sync_app from path
            if sync_app_path in sys.path:
                sys.path.remove(sync_app_path)
                
    except Exception as e:
        logger.error(f"Manual approval re-evaluation failed: {str(e)}")
        flash(f"Re-evaluation failed: {str(e)}", "error")
    
    return redirect(url_for('approval.list_requests'))
