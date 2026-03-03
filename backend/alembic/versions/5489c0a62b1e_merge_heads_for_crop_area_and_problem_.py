"""merge heads for crop_area and problem_area migration

Revision ID: 5489c0a62b1e
Revises: 20260123_crop_problem, 892e1e494d3f
Create Date: 2026-01-23 05:41:44.249008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5489c0a62b1e'
down_revision: Union[str, Sequence[str], None] = ('20260123_crop_problem', '892e1e494d3f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
