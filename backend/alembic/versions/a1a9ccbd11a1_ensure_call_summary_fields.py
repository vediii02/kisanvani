"""ensure_call_summary_fields

Revision ID: a1a9ccbd11a1
Revises: 28260f24ea3a
Create Date: 2026-03-09 18:42:31.830551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1a9ccbd11a1'
down_revision: Union[str, Sequence[str], None] = '28260f24ea3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
