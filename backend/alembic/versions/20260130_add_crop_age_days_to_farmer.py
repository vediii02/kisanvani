"""
Revision ID: 20260130_crop_age_days
Revises: 20260130_add_farmer_questions
Create Date: 2026-01-30
"""

revision = '20260130_crop_age_days'
down_revision = '20260130_add_farmer_questions'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('farmers', sa.Column('crop_age_days', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('farmers', 'crop_age_days')
