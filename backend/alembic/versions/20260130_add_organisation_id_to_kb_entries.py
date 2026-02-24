"""
Add organisation_id to kb_entries table for multi-org KB support
"""

revision = "20260130_add_organisation_id_to_kb_entries"
down_revision = None
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa



def upgrade():
    op.add_column('kb_entries', sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id'), nullable=True, index=True))

def downgrade():
    op.drop_column('kb_entries', 'organisation_id')
