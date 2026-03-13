"""add product metadata to kb

Revision ID: a2c3d4e5f6g7
Revises: f26eb22b3f29
Create Date: 2026-03-13 12:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'f26eb22b3f29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add product_id column
    op.add_column('knowledge_entries', sa.Column('product_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'knowledge_entries', 'products', ['product_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_knowledge_entries_product_id'), 'knowledge_entries', ['product_id'], unique=False)
    
    # Add metadata column
    op.add_column('knowledge_entries', sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add language column
    op.add_column('knowledge_entries', sa.Column('language', sa.String(length=10), server_default='hi', nullable=True))


def downgrade() -> None:
    op.drop_column('knowledge_entries', 'language')
    op.drop_column('knowledge_entries', 'metadata')
    op.drop_index(op.f('ix_knowledge_entries_product_id'), table_name='knowledge_entries')
    op.drop_constraint(None, 'knowledge_entries', type_='foreignkey')
    op.drop_column('knowledge_entries', 'product_id')
