"""Merge heads before adding budget tables

Revision ID: 11064205e552
Revises: 09ded262ecfc, fix_null_attachments
Create Date: 2025-07-06 15:29:08.595299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11064205e552'
down_revision: Union[str, Sequence[str], None] = ('09ded262ecfc', 'fix_null_attachments')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
