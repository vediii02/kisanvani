"""
Add organisation_id to kb_entries table for multi-org KB support
"""
from alembic import op
import sqlalchemy as sa

revision = "20260130_org_id_kb"
down_revision = "merge_advisory_heads_20260128"
branch_labels = None
depends_on = None



def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("kb_entries")}
    if "organisation_id" not in columns:
        op.add_column('kb_entries', sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id'), nullable=True))
    indexes = {idx["name"] for idx in inspector.get_indexes("kb_entries")}
    if "ix_kb_entries_organisation_id" not in indexes:
        op.create_index("ix_kb_entries_organisation_id", "kb_entries", ["organisation_id"], unique=False)

def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {idx["name"] for idx in inspector.get_indexes("kb_entries")}
    if "ix_kb_entries_organisation_id" in indexes:
        op.drop_index("ix_kb_entries_organisation_id", table_name="kb_entries")
    columns = {col["name"] for col in inspector.get_columns("kb_entries")}
    if "organisation_id" in columns:
        op.drop_column('kb_entries', 'organisation_id')
