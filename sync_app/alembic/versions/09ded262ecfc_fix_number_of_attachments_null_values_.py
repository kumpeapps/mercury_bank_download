"""fix_number_of_attachments_null_values_and_constraint

Revision ID: 09ded262ecfc
Revises: 874c4c7cb0fc
Create Date: 2025-07-05 19:31:56.971209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09ded262ecfc'
down_revision: Union[str, Sequence[str], None] = '874c4c7cb0fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix number_of_attachments NULL values and add NOT NULL constraint."""
    # Update existing NULL values to 0
    op.execute("UPDATE transactions SET number_of_attachments = 0 WHERE number_of_attachments IS NULL")
    
    # Add NOT NULL constraint with default value
    op.alter_column('transactions', 'number_of_attachments',
                   existing_type=sa.Integer(),
                   nullable=False,
                   server_default='0')


def downgrade() -> None:
    """Remove NOT NULL constraint and allow NULLs again."""
    # Remove NOT NULL constraint
    op.alter_column('transactions', 'number_of_attachments',
                   existing_type=sa.Integer(),
                   nullable=True,
                   server_default=None)
