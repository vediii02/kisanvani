"""merge login and summary heads

Revision ID: bdb309aa2f09
Revises: 087c6941121c, 889b39f75cc7
Create Date: 2026-03-08 10:10:24.171946

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bdb309aa2f09'
down_revision: Union[str, Sequence[str], None] = ('087c6941121c', '889b39f75cc7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
