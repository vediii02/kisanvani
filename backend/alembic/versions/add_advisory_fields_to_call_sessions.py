"""
Add advisory fields to call_sessions table

Revision ID: add_adv_fields_callsess
Revises: 
Create Date: 2026-01-28
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_adv_fields_callsess'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    from sqlalchemy import inspect, text
    from alembic import op
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('call_sessions')]
    if 'advisory_generated' not in columns:
        op.add_column('call_sessions', sa.Column('advisory_generated', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    if 'advisory_text' not in columns:
        op.add_column('call_sessions', sa.Column('advisory_text', sa.Text(), nullable=True))
    if 'raw_advisory' not in columns:
        op.add_column('call_sessions', sa.Column('raw_advisory', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('call_sessions', 'raw_advisory')
    op.drop_column('call_sessions', 'advisory_text')
    op.drop_column('call_sessions', 'advisory_generated')
