"""
Merge heads after adding advisory fields

Revision ID: merge_advisory_heads_20260128
Revises: add_advisory_fields_to_call_sessions, dfd1e5505626
Create Date: 2026-01-28
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'merge_advisory_heads_20260128'
down_revision = ('add_advisory_fields_to_call_sessions', 'dfd1e5505626')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
