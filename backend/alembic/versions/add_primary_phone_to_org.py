"""add primary phone to organisation

Revision ID: add_org_phone_002
Revises: add_phone_mgmt_001
Create Date: 2026-01-12 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_org_phone_002'
down_revision = 'add_phone_mgmt_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add primary_phone column to organisations table
    # This is the ONE phone number that farmers will call
    # Organisation can manage this from their dashboard
    op.add_column('organisations', 
        sa.Column('primary_phone', sa.String(20), nullable=True, unique=True)
    )
    
    # Add index for fast lookup during call routing
    op.create_index('idx_org_primary_phone', 'organisations', ['primary_phone'])


def downgrade():
    op.drop_index('idx_org_primary_phone', table_name='organisations')
    op.drop_column('organisations', 'primary_phone')
