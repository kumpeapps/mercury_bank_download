"""add_receipt_policies_table_with_data_migration

Revision ID: 874c4c7cb0fc
Revises: 3af8894c0ebc
Create Date: 2025-07-04 20:38:25.632193

"""
from typing import Sequence, Union
from datetime import datetime
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision: str = '874c4c7cb0fc'
down_revision: Union[str, Sequence[str], None] = '3af8894c0ebc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('alembic.migration')


def upgrade() -> None:
    """
    Upgrade schema and migrate data:
    
    1. Create the receipt_policies table
    2. For each existing account, insert a ReceiptPolicy row with:
       - Current receipt settings from the account
       - Start date of January 1, 2025
       - NULL end date (representing "still active")
    """
    # Create receipt_policies table
    op.create_table(
        'receipt_policies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('receipt_required_deposits', sa.String(length=20), nullable=True, default="none"),
        sa.Column('receipt_threshold_deposits', sa.Float(), nullable=True),
        sa.Column('receipt_required_charges', sa.String(length=20), nullable=True, default="none"),
        sa.Column('receipt_threshold_charges', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), 
                  onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name='fk_receipt_policy_account_id'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add index for faster lookups
    op.create_index('idx_receipt_policy_account_id', 'receipt_policies', ['account_id'], unique=False)
    op.create_index('idx_receipt_policy_dates', 'receipt_policies', ['start_date', 'end_date'], unique=False)
    
    # Copy data from accounts to the new receipt_policies table
    # We need to use SQLAlchemy ORM for this part
    conn = op.get_bind()
    session = Session(bind=conn)
    
    # Define temp models for the migration
    Base = declarative_base()
    
    class Account(Base):
        __tablename__ = 'accounts'
        id = sa.Column(sa.String(255), primary_key=True)
        receipt_required_deposits = sa.Column(sa.String(20))
        receipt_threshold_deposits = sa.Column(sa.Float, nullable=True)
        receipt_required_charges = sa.Column(sa.String(20))
        receipt_threshold_charges = sa.Column(sa.Float, nullable=True)
    
    class ReceiptPolicy(Base):
        __tablename__ = 'receipt_policies'
        id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
        account_id = sa.Column(sa.String(255), sa.ForeignKey("accounts.id"), nullable=False)
        start_date = sa.Column(sa.DateTime(timezone=True), nullable=False)
        end_date = sa.Column(sa.DateTime(timezone=True), nullable=True)
        receipt_required_deposits = sa.Column(sa.String(20))
        receipt_threshold_deposits = sa.Column(sa.Float, nullable=True)
        receipt_required_charges = sa.Column(sa.String(20))
        receipt_threshold_charges = sa.Column(sa.Float, nullable=True)
    
    # Migration start date - use current date
    start_date = datetime.now()
    
    # Get all accounts
    accounts = session.query(Account).all()
    logger.info(f"Found {len(accounts)} accounts to create receipt policies for")
    
    # For each account, create a receipt policy with the current settings
    policy_count = 0
    for account in accounts:
        policy = ReceiptPolicy(
            account_id=account.id,
            start_date=start_date,
            end_date=None,  # NULL means still active
            receipt_required_deposits=account.receipt_required_deposits or "none",
            receipt_threshold_deposits=account.receipt_threshold_deposits,
            receipt_required_charges=account.receipt_required_charges or "none",
            receipt_threshold_charges=account.receipt_threshold_charges
        )
        session.add(policy)
        policy_count += 1
    
    # Explicitly commit the changes to ensure they're saved
    session.flush()
    session.commit()
    
    logger.info(f"Created {policy_count} receipt policies during migration")


def downgrade() -> None:
    """
    Downgrade schema - drop the receipt_policies table.
    Note: This will delete all receipt policy history.
    """
    op.drop_index('idx_receipt_policy_dates', table_name='receipt_policies')
    op.drop_index('idx_receipt_policy_account_id', table_name='receipt_policies')
    op.drop_table('receipt_policies')
