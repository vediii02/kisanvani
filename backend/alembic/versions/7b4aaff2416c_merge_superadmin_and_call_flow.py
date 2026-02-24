"""merge superadmin and call flow

Revision ID: 7b4aaff2416c
Revises: 002_superadmin_platform, 003_call_flow
Create Date: 2026-01-11 16:08:39.616413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b4aaff2416c'
down_revision: Union[str, Sequence[str], None] = ('002_superadmin_platform', '003_call_flow')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
