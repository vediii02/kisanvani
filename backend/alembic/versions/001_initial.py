"""Initial migration with all models

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=200), nullable=True),
    sa.Column('hashed_password', sa.String(length=500), nullable=False),
    sa.Column('full_name', sa.String(length=200), nullable=True),
    sa.Column('role', sa.String(length=50), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    op.create_table('farmers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('phone_number', sa.String(length=15), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('village', sa.String(length=200), nullable=True),
    sa.Column('district', sa.String(length=200), nullable=True),
    sa.Column('state', sa.String(length=200), nullable=True),
    sa.Column('crop_type', sa.String(length=200), nullable=True),
    sa.Column('land_size', sa.String(length=50), nullable=True),
    sa.Column('language', sa.String(length=10), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', name='farmerstatus'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_farmers_id'), 'farmers', ['id'], unique=False)
    op.create_index(op.f('ix_farmers_phone_number'), 'farmers', ['phone_number'], unique=True)
    
    op.create_table('kb_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('crop_name', sa.String(length=100), nullable=True),
    sa.Column('problem_type', sa.String(length=100), nullable=True),
    sa.Column('solution_steps', sa.Text(), nullable=True),
    sa.Column('tags', sa.Text(), nullable=True),
    sa.Column('is_approved', sa.Boolean(), nullable=True),
    sa.Column('is_banned', sa.Boolean(), nullable=True),
    sa.Column('language', sa.String(length=10), nullable=True),
    sa.Column('created_by', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kb_entries_id'), 'kb_entries', ['id'], unique=False)
    
    op.create_table('call_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.String(length=100), nullable=False),
    sa.Column('farmer_id', sa.Integer(), nullable=True),
    sa.Column('phone_number', sa.String(length=15), nullable=False),
    sa.Column('provider_name', sa.String(length=50), nullable=True),
    sa.Column('provider_call_id', sa.String(length=200), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'COMPLETED', 'FAILED', name='callstatus'), nullable=True),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['farmer_id'], ['farmers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_call_sessions_id'), 'call_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_call_sessions_session_id'), 'call_sessions', ['session_id'], unique=True)
    
    op.create_table('cases',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('farmer_id', sa.Integer(), nullable=False),
    sa.Column('problem_text', sa.Text(), nullable=False),
    sa.Column('problem_category', sa.String(length=100), nullable=True),
    sa.Column('crop_name', sa.String(length=100), nullable=True),
    sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'RESOLVED', 'ESCALATED', name='casestatus'), nullable=True),
    sa.Column('confidence_score', sa.String(length=10), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['farmer_id'], ['farmers.id'], ),
    sa.ForeignKeyConstraint(['session_id'], ['call_sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cases_id'), 'cases', ['id'], unique=False)
    
    op.create_table('advisories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('case_id', sa.Integer(), nullable=False),
    sa.Column('advisory_text_hindi', sa.Text(), nullable=False),
    sa.Column('advisory_text_english', sa.Text(), nullable=True),
    sa.Column('immediate_action', sa.Text(), nullable=True),
    sa.Column('next_48_hours', sa.Text(), nullable=True),
    sa.Column('preventive_measures', sa.Text(), nullable=True),
    sa.Column('kb_entry_ids', sa.Text(), nullable=True),
    sa.Column('was_escalated', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_advisories_id'), 'advisories', ['id'], unique=False)
    
    op.create_table('escalations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('case_id', sa.Integer(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('confidence_score', sa.String(length=10), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'IN_REVIEW', 'RESOLVED', 'REJECTED', name='escalationstatus'), nullable=True),
    sa.Column('assigned_to', sa.String(length=100), nullable=True),
    sa.Column('resolution_notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_escalations_id'), 'escalations', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_escalations_id'), table_name='escalations')
    op.drop_table('escalations')
    op.drop_index(op.f('ix_advisories_id'), table_name='advisories')
    op.drop_table('advisories')
    op.drop_index(op.f('ix_cases_id'), table_name='cases')
    op.drop_table('cases')
    op.drop_index(op.f('ix_call_sessions_session_id'), table_name='call_sessions')
    op.drop_index(op.f('ix_call_sessions_id'), table_name='call_sessions')
    op.drop_table('call_sessions')
    op.drop_index(op.f('ix_kb_entries_id'), table_name='kb_entries')
    op.drop_table('kb_entries')
    op.drop_index(op.f('ix_farmers_phone_number'), table_name='farmers')
    op.drop_index(op.f('ix_farmers_id'), table_name='farmers')
    op.drop_table('farmers')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
