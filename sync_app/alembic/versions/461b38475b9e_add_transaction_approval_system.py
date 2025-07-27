"""Add transaction approval system

Revision ID: 461b38475b9e
Revises: b5ed68a6aa24
Create Date: 2025-07-25 16:54:01.244197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '461b38475b9e'
down_revision: Union[str, Sequence[str], None] = 'b5ed68a6aa24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Add approval status columns to transactions table
    op.add_column('transactions', sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='not_required'))
    op.add_column('transactions', sa.Column('approval_id', sa.Integer(), nullable=True))
    
    # Create transaction_restrictions table
    op.create_table('transaction_restrictions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.String(length=255), nullable=False),
        sa.Column('mercury_account_id', sa.Integer(), nullable=False),
        sa.Column('restriction_type', sa.String(length=50), nullable=False),
        sa.Column('amount_threshold', sa.Float(), nullable=True),
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('subcategory', sa.String(length=255), nullable=True),
        sa.Column('approvers', sa.Text(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['mercury_account_id'], ['mercury_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_transaction_restrictions_account_id'), 'transaction_restrictions', ['account_id'], unique=False)
    op.create_index(op.f('idx_transaction_restrictions_mercury_account_id'), 'transaction_restrictions', ['mercury_account_id'], unique=False)
    op.create_index(op.f('idx_transaction_restrictions_is_active'), 'transaction_restrictions', ['is_active'], unique=False)
    op.create_index(op.f('idx_transaction_restrictions_start_date'), 'transaction_restrictions', ['start_date'], unique=False)
    op.create_index(op.f('idx_transaction_restrictions_end_date'), 'transaction_restrictions', ['end_date'], unique=False)
    
    # Create transaction_approval_requests table
    op.create_table('transaction_approval_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('restriction_id', sa.Integer(), nullable=False),
        sa.Column('requested_by_user_id', sa.Integer(), nullable=False),
        sa.Column('max_transactions', sa.Integer(), nullable=True),
        sa.Column('max_amount', sa.Float(), nullable=True),
        sa.Column('approval_start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approval_end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('category_filter', sa.String(length=255), nullable=True),
        sa.Column('subcategory_filter', sa.String(length=255), nullable=True),
        sa.Column('request_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('approved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('approval_decision_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['restriction_id'], ['transaction_restrictions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_transaction_approval_requests_restriction_id'), 'transaction_approval_requests', ['restriction_id'], unique=False)
    op.create_index(op.f('idx_transaction_approval_requests_requested_by_user_id'), 'transaction_approval_requests', ['requested_by_user_id'], unique=False)
    op.create_index(op.f('idx_transaction_approval_requests_status'), 'transaction_approval_requests', ['status'], unique=False)
    op.create_index(op.f('idx_transaction_approval_requests_approval_start_date'), 'transaction_approval_requests', ['approval_start_date'], unique=False)
    op.create_index(op.f('idx_transaction_approval_requests_approval_end_date'), 'transaction_approval_requests', ['approval_end_date'], unique=False)
    
    # Create transaction_approvals table
    op.create_table('transaction_approvals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.String(length=255), nullable=False),
        sa.Column('max_transactions', sa.Integer(), nullable=True),
        sa.Column('max_amount', sa.Float(), nullable=True),
        sa.Column('used_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('used_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('approval_start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approval_end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('category_filter', sa.String(length=255), nullable=True),
        sa.Column('subcategory_filter', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['request_id'], ['transaction_approval_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_transaction_approvals_request_id'), 'transaction_approvals', ['request_id'], unique=False)
    op.create_index(op.f('idx_transaction_approvals_account_id'), 'transaction_approvals', ['account_id'], unique=False)
    op.create_index(op.f('idx_transaction_approvals_is_active'), 'transaction_approvals', ['is_active'], unique=False)
    op.create_index(op.f('idx_transaction_approvals_approval_start_date'), 'transaction_approvals', ['approval_start_date'], unique=False)
    op.create_index(op.f('idx_transaction_approvals_approval_end_date'), 'transaction_approvals', ['approval_end_date'], unique=False)
    
    # Create transaction_approval_rules table
    op.create_table('transaction_approval_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.String(length=255), nullable=False),
        sa.Column('mercury_account_id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(length=255), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('amount_threshold', sa.Float(), nullable=True),
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('subcategory', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['mercury_account_id'], ['mercury_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_transaction_approval_rules_account_id'), 'transaction_approval_rules', ['account_id'], unique=False)
    op.create_index(op.f('idx_transaction_approval_rules_mercury_account_id'), 'transaction_approval_rules', ['mercury_account_id'], unique=False)
    op.create_index(op.f('idx_transaction_approval_rules_priority'), 'transaction_approval_rules', ['priority'], unique=False)
    op.create_index(op.f('idx_transaction_approval_rules_is_active'), 'transaction_approval_rules', ['is_active'], unique=False)
    
    # Create transaction_approval_logs table
    op.create_table('transaction_approval_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('approval_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['approval_id'], ['transaction_approvals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_transaction_approval_logs_approval_id'), 'transaction_approval_logs', ['approval_id'], unique=False)
    op.create_index(op.f('idx_transaction_approval_logs_transaction_id'), 'transaction_approval_logs', ['transaction_id'], unique=False)
    op.create_index(op.f('idx_transaction_approval_logs_used_at'), 'transaction_approval_logs', ['used_at'], unique=False)
    
    # Create notification_logs table
    op.create_table('notification_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('notification_type', sa.String(length=100), nullable=False),
        sa.Column('recipient_type', sa.String(length=50), nullable=False),
        sa.Column('recipient_address', sa.String(length=500), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_id', sa.Integer(), nullable=True),
        sa.Column('related_type', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_notification_logs_notification_type'), 'notification_logs', ['notification_type'], unique=False)
    op.create_index(op.f('idx_notification_logs_recipient_type'), 'notification_logs', ['recipient_type'], unique=False)
    op.create_index(op.f('idx_notification_logs_status'), 'notification_logs', ['status'], unique=False)
    op.create_index(op.f('idx_notification_logs_created_at'), 'notification_logs', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('notification_logs')
    op.drop_table('transaction_approval_logs')
    op.drop_table('transaction_approval_rules')
    op.drop_table('transaction_approvals')
    op.drop_table('transaction_approval_requests')
    op.drop_table('transaction_restrictions')
    op.drop_column('transactions', 'approval_id')
    op.drop_column('transactions', 'approval_status')
