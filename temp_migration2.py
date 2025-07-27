"""Add name and account_ids to transaction restrictions

Revision ID: 141e7b7e4a34
Revises: 461b38475b9e
Create Date: 2025-07-25 23:13:40.273225

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '141e7b7e4a34'
down_revision: Union[str, Sequence[str], None] = '461b38475b9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if columns already exist, if not add them
    connection = op.get_bind()
    
    # Check if name column exists
    result = connection.execute(sa.text("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'transaction_restrictions' 
        AND TABLE_SCHEMA = DATABASE() 
        AND COLUMN_NAME = 'name'
    """)).fetchone()
    
    if not result:
        op.add_column('transaction_restrictions', sa.Column('name', sa.String(255), nullable=True))
    
    # Check if account_ids column exists
    result = connection.execute(sa.text("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'transaction_restrictions' 
        AND TABLE_SCHEMA = DATABASE() 
        AND COLUMN_NAME = 'account_ids'
    """)).fetchone()
    
    if not result:
        op.add_column('transaction_restrictions', sa.Column('account_ids', sa.Text(), nullable=True))
    
    # Populate name and account_ids for existing records that don't have them
    op.execute(sa.text("UPDATE transaction_restrictions SET name = CONCAT('Restriction #', id) WHERE name IS NULL"))
    op.execute(sa.text("UPDATE transaction_restrictions SET account_ids = account_id WHERE account_ids IS NULL"))
    
    # Make the new columns non-nullable using MySQL syntax
    op.execute(sa.text("ALTER TABLE transaction_restrictions MODIFY name VARCHAR(255) NOT NULL"))
    op.execute(sa.text("ALTER TABLE transaction_restrictions MODIFY account_ids TEXT NOT NULL"))
    
    # Check if account_id column still exists before dropping it
    result = connection.execute(sa.text("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'transaction_restrictions' 
        AND TABLE_SCHEMA = DATABASE() 
        AND COLUMN_NAME = 'account_id'
    """)).fetchone()
    
    if result:
        op.drop_column('transaction_restrictions', 'account_id')


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the account_id column
    op.add_column('transaction_restrictions', sa.Column('account_id', sa.String(255), nullable=True))
    
    # Populate account_id with the first account from account_ids
    op.execute("""
        UPDATE transaction_restrictions 
        SET account_id = SUBSTRING_INDEX(account_ids, ',', 1) 
        WHERE account_id IS NULL
    """)
    
    # Make account_id non-nullable using MySQL syntax
    op.execute("ALTER TABLE transaction_restrictions MODIFY account_id VARCHAR(255) NOT NULL")
    
    # Drop the new columns
    op.drop_column('transaction_restrictions', 'account_ids')
    op.drop_column('transaction_restrictions', 'name')
