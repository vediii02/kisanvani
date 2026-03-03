"""add_missing_company_fields

Revision ID: b51720004773
Revises: 89b2892ff479
Create Date: 2026-03-03 11:57:55.257360

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b51720004773'
down_revision: Union[str, Sequence[str], None] = '89b2892ff479'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('companies', sa.Column('website_link', sa.String(length=500), nullable=True))
    op.add_column('companies', sa.Column('description', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('companies', 'description')
    op.drop_column('companies', 'website_link')
