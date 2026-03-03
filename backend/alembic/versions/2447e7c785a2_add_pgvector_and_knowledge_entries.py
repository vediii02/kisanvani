"""Add pgvector and knowledge entries

Revision ID: 2447e7c785a2
Revises: ac1c1e5caf25
Create Date: 2026-02-27 12:00:31.437358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2447e7c785a2'
down_revision: Union[str, Sequence[str], None] = 'ac1c1e5caf25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create vector extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    
    # Create knowledge_entries table
    op.create_table(
        'knowledge_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crop', sa.String(length=100), nullable=True),
        sa.Column('problem_type', sa.String(length=100), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add pgvector column manually
    op.execute('ALTER TABLE "knowledge_entries" ADD COLUMN "embedding" vector(1536);')
    
    # Create indexes
    op.create_index(op.f('ix_knowledge_entries_id'), 'knowledge_entries', ['id'], unique=False)
    op.create_index(op.f('ix_knowledge_entries_crop'), 'knowledge_entries', ['crop'], unique=False)
    op.create_index(op.f('ix_knowledge_entries_problem_type'), 'knowledge_entries', ['problem_type'], unique=False)

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_knowledge_entries_problem_type'), table_name='knowledge_entries')
    op.drop_index(op.f('ix_knowledge_entries_crop'), table_name='knowledge_entries')
    op.drop_index(op.f('ix_knowledge_entries_id'), table_name='knowledge_entries')
    op.drop_table('knowledge_entries')
    op.execute('DROP EXTENSION IF EXISTS vector;')
