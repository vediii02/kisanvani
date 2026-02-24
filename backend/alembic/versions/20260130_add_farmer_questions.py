"""
Revision ID: 20260130_add_farmer_questions
Revises: 
Create Date: 2026-01-30
"""

revision = '20260130_add_farmer_questions'
down_revision = 'merge_advisory_heads_20260128'
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'farmer_questions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('farmer_id', sa.Integer, sa.ForeignKey('farmers.id'), nullable=False),
        sa.Column('call_sid', sa.String(64), nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('answer_text', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
    )

def downgrade():
    op.drop_table('farmer_questions')
