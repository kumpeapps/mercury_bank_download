"""Baseline migration for existing database

Revision ID: 3af8894c0ebc
Revises: 599ce2f74abb
Create Date: 2025-07-04 14:10:41.344934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3af8894c0ebc'
down_revision: Union[str, Sequence[str], None] = '599ce2f74abb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
