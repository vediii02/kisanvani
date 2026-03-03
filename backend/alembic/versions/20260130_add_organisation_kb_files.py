"""
Alembic migration for organisation_kb_files table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260130_org_kb_files'
down_revision = '20260130_org_id_kb'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'organisation_kb_files',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id'), nullable=False, index=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
    )

def downgrade():
    op.drop_table('organisation_kb_files')
