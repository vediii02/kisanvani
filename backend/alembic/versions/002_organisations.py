"""
Create multi-tenant organisation tables
Revision ID: 002_organisations
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

revision = '002_organisations'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create organisations table
    op.create_table(
        'organisations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('domain', sa.String(200), unique=True, nullable=True),
        sa.Column('status', sa.String(50), default='active', nullable=False),
        sa.Column('plan_type', sa.String(50), default='basic', nullable=False),
        sa.Column('phone_numbers', sa.Text(), nullable=True),  # JSON array
        sa.Column('created_at', sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc), nullable=True),
    )
    
    # 2. Create organisation_phone_numbers table
    op.create_table(
        'organisation_phone_numbers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('phone_number', sa.String(20), unique=True, nullable=False),
        sa.Column('channel', sa.String(20), default='voice', nullable=False),  # voice, whatsapp, sms
        sa.Column('status', sa.String(20), default='active', nullable=False),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    )
    
    # 3. Create brands table
    op.create_table(
        'brands',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc), nullable=True),
    )
    
    # 4. Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('brand_id', sa.Integer(), sa.ForeignKey('brands.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),  # pesticide, fertilizer, seed, equipment
        sa.Column('sub_category', sa.String(100), nullable=True),  # insecticide, fungicide, etc
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_crops', sa.Text(), nullable=True),  # JSON array
        sa.Column('target_problems', sa.Text(), nullable=True),  # JSON array (pest names, diseases)
        sa.Column('dosage', sa.Text(), nullable=True),
        sa.Column('usage_instructions', sa.Text(), nullable=True),
        sa.Column('safety_precautions', sa.Text(), nullable=True),
        sa.Column('price_range', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc), nullable=True),
    )
    
    # 5. Create organisation_settings table
    op.create_table(
        'organisation_settings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('ai_model', sa.String(100), default='gpt-4', nullable=True),
        sa.Column('default_language', sa.String(20), default='hi', nullable=True),
        sa.Column('supported_languages', sa.Text(), nullable=True),  # JSON array
        sa.Column('crop_focus', sa.Text(), nullable=True),  # JSON array
        sa.Column('monthly_call_limit', sa.Integer(), default=1000, nullable=True),
        sa.Column('features_enabled', sa.Text(), nullable=True),  # JSON object
        sa.Column('ai_prompt_template', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc), nullable=True),
    )
    
    # 6. Add organisation_id to existing tables
    op.add_column('users', sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id', ondelete='SET NULL'), nullable=True))
    op.add_column('farmers', sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=True))
    op.add_column('call_sessions', sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=True))
    op.add_column('cases', sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=True))
    op.add_column('kb_entries', sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=True))
    op.add_column('escalations', sa.Column('organisation_id', sa.Integer(), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=True))
    
    # 7. Create default organisation for existing data
    op.execute("""
        INSERT INTO organisations (name, domain, status, plan_type, created_at)
        VALUES ('Default Organisation', 'default.kisanvani.ai', 'active', 'enterprise', NOW())
    """)
    
    # 8. Update existing records with default organisation_id
    op.execute("UPDATE users SET organisation_id = 1 WHERE organisation_id IS NULL")
    op.execute("UPDATE farmers SET organisation_id = 1 WHERE organisation_id IS NULL")
    op.execute("UPDATE call_sessions SET organisation_id = 1 WHERE organisation_id IS NULL")
    op.execute("UPDATE cases SET organisation_id = 1 WHERE organisation_id IS NULL")
    op.execute("UPDATE kb_entries SET organisation_id = 1 WHERE organisation_id IS NULL")
    op.execute("UPDATE escalations SET organisation_id = 1 WHERE organisation_id IS NULL")
    
    # 9. Create indexes for better performance
    op.create_index('idx_users_org_id', 'users', ['organisation_id'])
    op.create_index('idx_farmers_org_id', 'farmers', ['organisation_id'])
    op.create_index('idx_call_sessions_org_id', 'call_sessions', ['organisation_id'])
    op.create_index('idx_kb_entries_org_id', 'kb_entries', ['organisation_id'])
    op.create_index('idx_products_org_id', 'products', ['organisation_id'])
    op.create_index('idx_brands_org_id', 'brands', ['organisation_id'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_brands_org_id', 'brands')
    op.drop_index('idx_products_org_id', 'products')
    op.drop_index('idx_kb_entries_org_id', 'kb_entries')
    op.drop_index('idx_call_sessions_org_id', 'call_sessions')
    op.drop_index('idx_farmers_org_id', 'farmers')
    op.drop_index('idx_users_org_id', 'users')
    
    # Drop organisation_id columns
    op.drop_column('escalations', 'organisation_id')
    op.drop_column('kb_entries', 'organisation_id')
    op.drop_column('cases', 'organisation_id')
    op.drop_column('call_sessions', 'organisation_id')
    op.drop_column('farmers', 'organisation_id')
    op.drop_column('users', 'organisation_id')
    
    # Drop tables
    op.drop_table('organisation_settings')
    op.drop_table('products')
    op.drop_table('brands')
    op.drop_table('organisation_phone_numbers')
    op.drop_table('organisations')
