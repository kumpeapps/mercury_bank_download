"""Fix number_of_attachments null values

Revision ID: fix_null_attachments
Revises: 
Create Date: 2025-01-05 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_null_attachments'
down_revision = None  # Will be auto-populated by alembic
depends_on = None


def upgrade():
    """Fix NULL number_of_attachments values and add NOT NULL constraint"""
    
    # Update existing NULL values to 0
    op.execute("""
        UPDATE transactions 
        SET number_of_attachments = 0 
        WHERE number_of_attachments IS NULL
    """)
    
    # Add NOT NULL constraint and set default value
    op.alter_column('transactions', 'number_of_attachments',
                   existing_type=sa.Integer(),
                   nullable=False,
                   server_default='0')


def downgrade():
    """Remove NOT NULL constraint"""
    
    # Remove NOT NULL constraint and default
    op.alter_column('transactions', 'number_of_attachments',
                   existing_type=sa.Integer(),
                   nullable=True,
                   server_default=None)
