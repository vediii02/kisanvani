"""merge_heads_20260130

Revision ID: 92b079f0dbab
Revises: 20260130_crop_age_days, 20260130_org_kb_files
Create Date: 2026-02-25 05:35:14.703064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92b079f0dbab'
down_revision: Union[str, Sequence[str], None] = ('20260130_crop_age_days', '20260130_org_kb_files')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
