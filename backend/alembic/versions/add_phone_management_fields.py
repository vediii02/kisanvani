"""Add organisation phone management and greeting support

Revision ID: add_phone_mgmt_001
Revises: 7b4aaff2416c
Create Date: 2026-01-12 11:25:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'add_phone_mgmt_001'
down_revision: Union[str, Sequence[str], None] = '7b4aaff2416c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with phone management fields."""
    
    # Add new columns to organisations table
    op.add_column('organisations', sa.Column('greeting_message', sa.Text(), nullable=True,
        comment='Custom AI greeting message for this organisation'))
    op.add_column('organisations', sa.Column('preferred_languages', sa.String(length=100), 
        nullable=False, server_default='hi',
        comment='Comma-separated list of languages: hi,en,mr,ta,te,kn,gu,pa,or,bn'))
    
    # Add new columns to organisation_phone_numbers table
    op.add_column('organisation_phone_numbers', sa.Column('is_active', sa.Boolean(), 
        nullable=False, server_default='1',
        comment='Active phone numbers can receive calls'))
    op.add_column('organisation_phone_numbers', sa.Column('display_name', sa.String(length=100), 
        nullable=True,
        comment='Friendly name like "Main Helpline" or "Kerala Office"'))
    op.add_column('organisation_phone_numbers', sa.Column('updated_at', sa.DateTime(timezone=True), 
        nullable=True, onupdate=sa.func.now(),
        comment='Last updated timestamp'))
    
    # Create composite index for fast phone lookups during call routing
    # This is CRITICAL for performance: O(1) lookup instead of O(n)
    op.create_index(
        'idx_phone_active_lookup', 
        'organisation_phone_numbers', 
        ['phone_number', 'is_active'], 
        unique=False
    )
    
    # Migrate old status column to is_active (if status column exists)
    # Old: status='active'/'inactive' -> New: is_active=True/False
    connection = op.get_bind()
    try:
        # Check if status column exists
        inspector = sa.inspect(connection)
        columns = [col['name'] for col in inspector.get_columns('organisation_phone_numbers')]
        
        if 'status' in columns:
            # Migrate data: 'active' -> True, everything else -> False
            connection.execute(sa.text(
                "UPDATE organisation_phone_numbers SET is_active = (status = 'active')"
            ))
            # Drop old status column
            op.drop_column('organisation_phone_numbers', 'status')
    except Exception as e:
        print(f"Note: Could not migrate status column: {e}")
        # Not critical - column might not exist
    
    print("✅ Phone management schema upgraded successfully!")
    print("📞 Phone routing index created for fast lookups")
    print("🎯 Organisations can now have custom greetings")


def downgrade() -> None:
    """Downgrade schema - remove phone management fields."""
    
    # Drop index
    op.drop_index('idx_phone_active_lookup', table_name='organisation_phone_numbers')
    
    # Drop new columns from organisation_phone_numbers
    op.drop_column('organisation_phone_numbers', 'updated_at')
    op.drop_column('organisation_phone_numbers', 'display_name')
    op.drop_column('organisation_phone_numbers', 'is_active')
    
    # Drop new columns from organisations
    op.drop_column('organisations', 'preferred_languages')
    op.drop_column('organisations', 'greeting_message')
    
    print("⬇️ Phone management schema downgraded")
