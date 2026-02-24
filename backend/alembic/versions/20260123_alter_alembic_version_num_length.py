"""
Alter alembic_version.version_num to VARCHAR(255)

Revision ID: 20260123_alter_alembic_version_num_length
Revises: 892e1e494d3f
Create Date: 2026-01-23
"""
from alembic import op
import sqlalchemy as sa

revision = '20260123_alter_alembic_version_num_length'
down_revision = '892e1e494d3f'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('alembic_version', 'version_num', type_=sa.String(length=255))

def downgrade():
    op.alter_column('alembic_version', 'version_num', type_=sa.String(length=32))
