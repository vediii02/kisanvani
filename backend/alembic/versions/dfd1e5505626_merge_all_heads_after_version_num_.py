"""merge all heads after version_num length fix

Revision ID: dfd1e5505626
Revises: 20260123_alembic_vnum, 5489c0a62b1e
Create Date: 2026-01-23 05:43:25.353849

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfd1e5505626'
down_revision: Union[str, Sequence[str], None] = ('20260123_alembic_vnum', '5489c0a62b1e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
