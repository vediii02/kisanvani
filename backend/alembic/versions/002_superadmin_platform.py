"""Super Admin Platform - Audit Logs, Config, Banned Products

Revision ID: 002_superadmin_platform
Revises: 001_initial
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002_superadmin_platform'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('action_category', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='info'),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'], unique=False)
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'], unique=False)
    op.create_index('idx_audit_category', 'audit_logs', ['action_category'], unique=False)
    op.create_index('idx_audit_severity', 'audit_logs', ['severity'], unique=False)

    # Create platform_config table
    op.create_table('platform_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ai_confidence_threshold', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('max_call_duration_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('default_language', sa.String(length=10), nullable=False, server_default='hi'),
        sa.Column('stt_provider', sa.String(length=50), nullable=False, server_default='google'),
        sa.Column('tts_provider', sa.String(length=50), nullable=False, server_default='google'),
        sa.Column('llm_model', sa.String(length=100), nullable=False, server_default='gpt-4'),
        sa.Column('rag_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('rag_top_k', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('enable_product_safety_check', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_escalate_low_confidence', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('min_confidence_for_product_recommendation', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # Create banned_products table
    op.create_table('banned_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(length=200), nullable=False),
        sa.Column('chemical_name', sa.String(length=200), nullable=True),
        sa.Column('ban_reason', sa.Text(), nullable=False),
        sa.Column('regulatory_reference', sa.String(length=255), nullable=True),
        sa.Column('banned_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('banned_by_user_id', sa.Integer(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['banned_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('idx_banned_product_name', 'banned_products', ['product_name'], unique=False)
    op.create_index('idx_banned_active', 'banned_products', ['is_active'], unique=False)

    # Insert default platform config
    op.execute("""
        INSERT INTO platform_config (
            ai_confidence_threshold,
            max_call_duration_minutes,
            default_language,
            stt_provider,
            tts_provider,
            llm_model,
            rag_enabled,
            rag_top_k,
            enable_product_safety_check,
            auto_escalate_low_confidence,
            min_confidence_for_product_recommendation
        ) VALUES (
            0.7,
            30,
            'hi',
            'google',
            'google',
            'gpt-4',
            true,
            5,
            true,
            true,
            0.8
        )
    """)


def downgrade():
    op.drop_table('banned_products')
    op.drop_table('platform_config')
    op.drop_table('audit_logs')
