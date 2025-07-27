"""Add name field and multi-account support to transaction restrictions

Revision ID: 3b905239230d
Revises: 461b38475b9e
Create Date: 2025-01-25 18:20:07.176923

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3b905239230d'
down_revision: Union[str, Sequence[str], None] = '461b38475b9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add name field and multi-account support."""
    # Check if columns already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('transaction_restrictions')]
    
    # Add name field if it doesn't exist
    if 'name' not in columns:
        op.add_column('transaction_restrictions', 
                      sa.Column('name', sa.String(255), nullable=True))
        print("Added 'name' column to transaction_restrictions")
    else:
        print("Column 'name' already exists, skipping")
    
    # Add account_ids field if it doesn't exist
    if 'account_ids' not in columns:
        op.add_column('transaction_restrictions',
                      sa.Column('account_ids', sa.Text, nullable=True))
        print("Added 'account_ids' column to transaction_restrictions")
    else:
        print("Column 'account_ids' already exists, skipping")
    
    # Migrate existing data only if columns were just added
    if 'account_ids' not in columns and 'account_id' in columns:
        op.execute("""
            UPDATE transaction_restrictions 
            SET account_ids = CAST(account_id AS CHAR),
                name = CONCAT('Restriction for Account ', account_id, ' - ', DATE_FORMAT(created_at, '%Y-%m-%d'))
            WHERE account_id IS NOT NULL AND (account_ids IS NULL OR account_ids = '')
        """)
        print("Migrated existing data from account_id to account_ids")
    
    # Provide default names for existing records that don't have them
    op.execute("""
        UPDATE transaction_restrictions 
        SET name = CONCAT('Transaction Restriction - ', DATE_FORMAT(created_at, '%Y-%m-%d %H:%i'))
        WHERE name IS NULL OR name = ''
    """)
    
    # Make the new fields non-nullable after data migration
    op.alter_column('transaction_restrictions', 'name', nullable=False)
    op.alter_column('transaction_restrictions', 'account_ids', nullable=False)
    
    # Drop the old foreign key constraint and account_id column if they exist
    if 'account_id' in columns:
        try:
            op.drop_constraint('transaction_restrictions_ibfk_1', 'transaction_restrictions', type_='foreignkey')
            print("Dropped foreign key constraint")
        except:
            pass  # Constraint might not exist or have different name
            
        op.drop_column('transaction_restrictions', 'account_id')
        print("Dropped 'account_id' column")


def downgrade() -> None:
    """Downgrade schema to restore single account_id field."""
    # Add back account_id column
    op.add_column('transaction_restrictions',
                  sa.Column('account_id', sa.Integer, nullable=True))
    
    # Migrate data back: take first account_id from account_ids
    op.execute("""
        UPDATE transaction_restrictions 
        SET account_id = CAST(SUBSTRING_INDEX(account_ids, ',', 1) AS UNSIGNED)
        WHERE account_ids IS NOT NULL AND account_ids != ''
    """)
    
    # Recreate foreign key constraint
    try:
        op.create_foreign_key('transaction_restrictions_ibfk_1', 
                             'transaction_restrictions', 'accounts',
                             ['account_id'], ['id'])
    except:
        pass  # May fail if referenced table structure is different
    
    # Drop the new columns
    op.drop_column('transaction_restrictions', 'account_ids')
    op.drop_column('transaction_restrictions', 'name')
