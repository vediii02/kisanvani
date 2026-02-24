"""
Add crop_area and problem_area columns to farmers table

Revision ID: 20260123_add_crop_and_problem_area_to_farmer
Revises: 003_call_flow
Create Date: 2026-01-23
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260123_add_crop_and_problem_area_to_farmer'
down_revision = '003_call_flow'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('farmers', sa.Column('crop_area', sa.String(length=100)))
    op.add_column('farmers', sa.Column('problem_area', sa.String(length=200)))

def downgrade():
    op.drop_column('farmers', 'problem_area')
    op.drop_column('farmers', 'crop_area')
