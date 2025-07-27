"""
Transaction Approval Web Interface Integration
This code should be added to the main app.py file to provide web interface
for the transaction approval system.
"""

# Add these routes to the existing app.py file

@app.route('/approval/restrictions')
@login_required
@admin_required
def approval_restrictions():
    """List all transaction restrictions."""
    db_session = Session()
    try:
        page = request.args.get('page', 1, type=int)
        
        # Get accounts user has access to
        if current_user.has_role('super-admin'):
            restrictions = db_session.query(TransactionRestriction).paginate(
                page=page, per_page=20, error_out=False
            )
        else:
            # Filter by accounts user has access to
            user = db_session.query(User).get(current_user.id)
            account_ids = [acc.id for acc in user.accounts]
            restrictions = db_session.query(TransactionRestriction).filter(
                TransactionRestriction.account_id.in_(account_ids)
            ).paginate(page=page, per_page=20, error_out=False)
        
        return render_template('approval/restrictions.html', restrictions=restrictions)
    finally:
        db_session.close()


@app.route('/approval/restrictions/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_approval_restriction():
    """Create a new transaction restriction."""
    db_session = Session()
    try:
        if request.method == 'POST':
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
                                     accounts=get_user_accounts(db_session),
                                     users=get_approver_users(db_session))
            
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
            
            db_session.add(restriction)
            db_session.commit()
            
            flash('Transaction restriction created successfully.', 'success')
            return redirect(url_for('approval_restrictions'))
        
        return render_template('approval/create_restriction.html', 
                             accounts=get_user_accounts(db_session),
                             users=get_approver_users(db_session))
    except Exception as e:
        flash(f'Error creating restriction: {str(e)}', 'error')
        db_session.rollback()
        return render_template('approval/create_restriction.html', 
                             accounts=get_user_accounts(db_session),
                             users=get_approver_users(db_session))
    finally:
        db_session.close()


@app.route('/approval/requests')
@login_required
def approval_requests():
    """List approval requests (pending, approved, denied)."""
    db_session = Session()
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all')
        
        # Base query
        query = db_session.query(TransactionApprovalRequest)
        
        # Filter by status if specified
        if status_filter != 'all':
            query = query.filter(TransactionApprovalRequest.status == status_filter)
        
        # Filter by user permissions
        if not current_user.has_role('super-admin'):
            # Show requests for accounts user has access to or requests they made
            user = db_session.query(User).get(current_user.id)
            account_ids = [acc.id for acc in user.accounts]
            query = query.join(TransactionRestriction).filter(
                (TransactionRestriction.account_id.in_(account_ids)) |
                (TransactionApprovalRequest.requested_by_user_id == current_user.id)
            )
        
        # Execute query with pagination
        requests = query.order_by(TransactionApprovalRequest.created_date.desc()).offset(
            (page - 1) * 20
        ).limit(20).all()
        
        return render_template('approval/requests.html', requests=requests, status_filter=status_filter)
    finally:
        db_session.close()


@app.route('/approval/requests/new', methods=['GET', 'POST'])
@login_required
def create_approval_request():
    """Create a new approval request."""
    db_session = Session()
    try:
        if request.method == 'POST':
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
                                     restrictions=get_user_restrictions(db_session))
            
            # Parse dates
            approval_start_date = datetime.strptime(approval_start_date, '%Y-%m-%d')
            approval_end_date = datetime.strptime(approval_end_date, '%Y-%m-%d')
            
            # Parse numeric fields
            max_transactions = int(max_transactions) if max_transactions else None
            max_amount = float(max_amount) if max_amount else None
            
            # Create approval request
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
            
            flash('Approval request submitted successfully.', 'success')
            return redirect(url_for('approval_requests'))
        
        return render_template('approval/create_request.html', 
                             restrictions=get_user_restrictions(db_session))
    except Exception as e:
        flash(f'Error creating approval request: {str(e)}', 'error')
        db_session.rollback()
        return render_template('approval/create_request.html', 
                             restrictions=get_user_restrictions(db_session))
    finally:
        db_session.close()


@app.route('/approval/requests/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_approval_request(request_id):
    """Approve an approval request."""
    db_session = Session()
    try:
        approval_request = db_session.query(TransactionApprovalRequest).get(request_id)
        
        if not approval_request:
            flash('Approval request not found.', 'error')
            return redirect(url_for('approval_requests'))
        
        # Check if user is authorized to approve this request
        if not can_approve_request(approval_request, current_user, db_session):
            flash('You are not authorized to approve this request.', 'error')
            return redirect(url_for('approval_requests'))
        
        if approval_request.status != 'pending':
            flash('This request has already been processed.', 'error')
            return redirect(url_for('approval_requests'))
        
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
        
        db_session.add(approval)
        db_session.commit()
        
        flash('Approval request approved successfully.', 'success')
        
    except Exception as e:
        flash(f'Error approving request: {str(e)}', 'error')
        db_session.rollback()
    finally:
        db_session.close()
    
    return redirect(url_for('approval_requests'))


@app.route('/approval/requests/<int:request_id>/deny', methods=['POST'])
@login_required
def deny_approval_request(request_id):
    """Deny an approval request."""
    db_session = Session()
    try:
        approval_request = db_session.query(TransactionApprovalRequest).get(request_id)
        
        if not approval_request:
            flash('Approval request not found.', 'error')
            return redirect(url_for('approval_requests'))
        
        # Check if user is authorized to approve this request
        if not can_approve_request(approval_request, current_user, db_session):
            flash('You are not authorized to deny this request.', 'error')
            return redirect(url_for('approval_requests'))
        
        if approval_request.status != 'pending':
            flash('This request has already been processed.', 'error')
            return redirect(url_for('approval_requests'))
        
        approval_notes = request.form.get('approval_notes', '')
        
        # Update request
        approval_request.status = 'denied'
        approval_request.approved_by_user_id = current_user.id
        approval_request.approval_decision_date = datetime.utcnow()
        approval_request.approval_notes = approval_notes
        
        db_session.commit()
        
        flash('Approval request denied.', 'success')
        
    except Exception as e:
        flash(f'Error denying request: {str(e)}', 'error')
        db_session.rollback()
    finally:
        db_session.close()
    
    return redirect(url_for('approval_requests'))


def get_user_accounts(db_session):
    """Get accounts the current user has access to."""
    if current_user.has_role('super-admin'):
        return db_session.query(Account).all()
    else:
        user = db_session.query(User).get(current_user.id)
        return user.accounts


def get_approver_users(db_session):
    """Get users who can be approvers."""
    return db_session.query(User).filter(User.is_active == True).all()


def get_user_restrictions(db_session):
    """Get restrictions for accounts the user has access to."""
    if current_user.has_role('super-admin'):
        return db_session.query(TransactionRestriction).filter(
            TransactionRestriction.is_active == True
        ).all()
    else:
        user = db_session.query(User).get(current_user.id)
        account_ids = [acc.id for acc in user.accounts]
        return db_session.query(TransactionRestriction).filter(
            TransactionRestriction.account_id.in_(account_ids),
            TransactionRestriction.is_active == True
        ).all()


def can_approve_request(approval_request, user, db_session):
    """Check if a user can approve a specific request."""
    if user.has_role('super-admin'):
        return True
    
    # Check if user is in the restriction's approver list
    approver_ids = approval_request.restriction.get_approver_list()
    return user.id in approver_ids
