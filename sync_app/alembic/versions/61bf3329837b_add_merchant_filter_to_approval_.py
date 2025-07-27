"""Add merchant_filter to approval requests and approvals

Revision ID: 61bf3329837b
Revises: 3b905239230d
Create Date: 2025-07-26 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61bf3329837b'
down_revision: Union[str, Sequence[str], None] = '3b905239230d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add merchant_filter column to transaction_approval_requests
    op.add_column('transaction_approval_requests', sa.Column('merchant_filter', sa.String(length=255), nullable=True))
    
    # Add merchant_filter column to transaction_approvals
    op.add_column('transaction_approvals', sa.Column('merchant_filter', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop merchant_filter columns
    op.drop_column('transaction_approvals', 'merchant_filter')
    op.drop_column('transaction_approval_requests', 'merchant_filter')