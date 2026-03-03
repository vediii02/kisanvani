"""Add website_link to organisation

Revision ID: 89b2892ff479
Revises: 350e6874ef31
Create Date: 2026-03-03 10:16:38.371891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89b2892ff479'
down_revision: Union[str, Sequence[str], None] = '350e6874ef31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('organisations', sa.Column('website_link', sa.String(length=500), nullable=True))
    op.add_column('organisations', sa.Column('description', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('organisations', 'description')
    op.drop_column('organisations', 'website_link')
