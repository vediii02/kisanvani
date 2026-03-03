"""Add call flow system tables

Revision ID: 003_call_flow
Revises: 002_organisations
Create Date: 2024-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '003_call_flow'
down_revision = '002_organisations'
branch_labels = None
depends_on = None


def upgrade():
    # Check and create tables only if they don't exist
    # Note: Some tables may already exist from earlier manual creation
    
    # 1-7: Skip existing tables (call_states, farmer_profile_questions, etc.)

    # 8. Call Transcripts
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    
    if 'call_transcripts' not in existing_tables:
        op.create_table(
            'call_transcripts',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('call_session_id', sa.Integer(), nullable=False),
            sa.Column('speaker', sa.Enum('AI', 'FARMER', 'EXPERT', name='speaker_enum'), nullable=False),
            sa.Column('transcript_text', sa.Text(), nullable=False),
            sa.Column('language_code', sa.String(10), default='hi-IN'),
            sa.Column('audio_duration_ms', sa.Integer(), nullable=True),
            sa.Column('confidence_score', sa.Float(), nullable=True),  # STT confidence
            sa.Column('spoken_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['call_session_id'], ['call_sessions.id'], ondelete='CASCADE'),
            sa.Index('idx_transcripts_call', 'call_session_id'),
            sa.Index('idx_transcripts_speaker', 'speaker')
        )

    # 9. Confidence Rules (for auto-escalation)
    if 'confidence_rules' not in existing_tables:
        op.create_table(
            'confidence_rules',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organisation_id', sa.Integer(), nullable=False),
            sa.Column('rule_name', sa.String(100), nullable=False),
            sa.Column('rule_type', sa.String(50), nullable=False),  # threshold, keyword, symptom_count
            sa.Column('threshold_value', sa.Float(), nullable=True),
            sa.Column('escalation_reason', sa.String(255), nullable=False),
            sa.Column('priority_boost', sa.Integer(), default=0),  # Increase escalation priority
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
            sa.Index('idx_confidence_rules_org', 'organisation_id')
        )

    # 10. Expert Actions (tracking expert interventions)
    if 'expert_actions' not in existing_tables:
        op.create_table(
            'expert_actions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('escalation_id', sa.Integer(), nullable=False),
            sa.Column('expert_user_id', sa.Integer(), nullable=False),
            sa.Column('action_type', sa.Enum(
                'VIEWED', 'ASSIGNED', 'NOTES_ADDED', 'ADVISORY_PROVIDED', 
                'CALLBACK_SCHEDULED', 'RESOLVED', 'REOPENED',
                name='expert_action_enum'
            ), nullable=False),
            sa.Column('action_notes', sa.Text(), nullable=True),
            sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['escalation_id'], ['escalations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['expert_user_id'], ['users.id'], ondelete='CASCADE'),
            sa.Index('idx_expert_actions_escalation', 'escalation_id'),
            sa.Index('idx_expert_actions_expert', 'expert_user_id')
        )

    # 11. Call Summaries (for SMS/WhatsApp)
    if 'call_summaries' not in existing_tables:
        op.create_table(
            'call_summaries',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('call_session_id', sa.Integer(), nullable=False),
            sa.Column('summary_text_hindi', sa.Text(), nullable=False),
            sa.Column('summary_text_english', sa.Text(), nullable=True),
            sa.Column('key_recommendations', sa.JSON(), nullable=True),  # Bullet points
            sa.Column('products_mentioned', sa.JSON(), nullable=True),  # Product IDs
            sa.Column('sms_sent', sa.Boolean(), default=False),
            sa.Column('sms_sent_at', sa.DateTime(), nullable=True),
            sa.Column('whatsapp_sent', sa.Boolean(), default=False),
            sa.Column('whatsapp_sent_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['call_session_id'], ['call_sessions.id'], ondelete='CASCADE'),
            sa.Index('idx_call_summaries_call', 'call_session_id')
        )

    # 12. Call Metrics (for analytics)
    if 'call_metrics' not in existing_tables:
        op.create_table(
            'call_metrics',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('call_session_id', sa.Integer(), nullable=False),
            sa.Column('organisation_id', sa.Integer(), nullable=False),
            sa.Column('total_duration_seconds', sa.Integer(), nullable=True),
            sa.Column('states_visited', sa.JSON(), nullable=True),  # [GREETING, PROFILING, ...]
            sa.Column('profiling_questions_completed', sa.Integer(), default=0),
            sa.Column('symptoms_detected', sa.Integer(), default=0),
            sa.Column('kb_entries_retrieved', sa.Integer(), default=0),
            sa.Column('advisory_confidence', sa.Float(), nullable=True),
            sa.Column('was_escalated', sa.Boolean(), default=False),
            sa.Column('escalation_reason', sa.String(255), nullable=True),
            sa.Column('farmer_satisfaction', sa.Integer(), nullable=True),  # 1-5 stars (post-call)
            sa.Column('call_outcome', sa.Enum(
                'COMPLETED', 'ABANDONED', 'ESCALATED', 'FAILED', 'CALLBACK_SCHEDULED',
                name='call_outcome_enum'
            ), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['call_session_id'], ['call_sessions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
            sa.Index('idx_call_metrics_call', 'call_session_id'),
            sa.Index('idx_call_metrics_org', 'organisation_id'),
            sa.Index('idx_call_metrics_outcome', 'call_outcome')
        )

    # Add new columns to existing tables
    # Add organisation_id and crop columns to cases table (check if exists first)
    existing_columns = [col['name'] for col in inspector.get_columns('cases')]
    
    if 'crop_name' not in existing_columns:
        op.add_column('cases', sa.Column('crop_name', sa.String(100), nullable=True))
    if 'crop_stage' not in existing_columns:
        op.add_column('cases', sa.Column('crop_stage', sa.String(50), nullable=True))
    if 'affected_area_acres' not in existing_columns:
        op.add_column('cases', sa.Column('affected_area_acres', sa.Float(), nullable=True))
    if 'problem_category' not in existing_columns:
        op.add_column('cases', sa.Column('problem_category', sa.String(100), nullable=True))
    
    # Add approval fields to products table
    existing_product_columns = [col['name'] for col in inspector.get_columns('products')]
    
    if 'approval_status' not in existing_product_columns:
        approval_status_enum = sa.Enum('pending', 'approved', 'banned', name='approval_status_enum')
        approval_status_enum.create(op.get_bind(), checkfirst=True)
        op.add_column('products', sa.Column('approval_status', approval_status_enum, server_default='pending'))
    if 'approved_by' not in existing_product_columns:
        op.add_column('products', sa.Column('approved_by', sa.Integer(), nullable=True))
    if 'approved_at' not in existing_product_columns:
        op.add_column('products', sa.Column('approved_at', sa.DateTime(), nullable=True))
    if 'ban_reason' not in existing_product_columns:
        op.add_column('products', sa.Column('ban_reason', sa.Text(), nullable=True))
    
    # Add embedding tracking to kb_entries
    existing_kb_columns = [col['name'] for col in inspector.get_columns('kb_entries')]
    
    if 'embedding_id' not in existing_kb_columns:
        op.add_column('kb_entries', sa.Column('embedding_id', sa.String(100), nullable=True))
    if 'embedding_model' not in existing_kb_columns:
        op.add_column('kb_entries', sa.Column('embedding_model', sa.String(100), nullable=True))
    if 'last_embedded_at' not in existing_kb_columns:
        op.add_column('kb_entries', sa.Column('last_embedded_at', sa.DateTime(), nullable=True))
    
    # Add phone number tracking to call_sessions
    existing_call_columns = [col['name'] for col in inspector.get_columns('call_sessions')]
    
    if 'from_phone' not in existing_call_columns:
        op.add_column('call_sessions', sa.Column('from_phone', sa.String(20), nullable=True))
    if 'to_phone' not in existing_call_columns:
        op.add_column('call_sessions', sa.Column('to_phone', sa.String(20), nullable=True))
    if 'exotel_call_sid' not in existing_call_columns:
        op.add_column('call_sessions', sa.Column('exotel_call_sid', sa.String(100), nullable=True))
    if 'call_direction' not in existing_call_columns:
        call_direction_enum = sa.Enum('inbound', 'outbound', name='call_direction_enum')
        call_direction_enum.create(op.get_bind(), checkfirst=True)
        op.add_column('call_sessions', sa.Column('call_direction', call_direction_enum, server_default='inbound'))


def downgrade():
    # Drop new columns from existing tables
    op.drop_column('call_sessions', 'call_direction')
    op.drop_column('call_sessions', 'exotel_call_sid')
    op.drop_column('call_sessions', 'to_phone')
    op.drop_column('call_sessions', 'from_phone')
    
    op.drop_column('kb_entries', 'last_embedded_at')
    op.drop_column('kb_entries', 'embedding_model')
    op.drop_column('kb_entries', 'embedding_id')
    
    op.drop_column('products', 'ban_reason')
    op.drop_column('products', 'approved_at')
    op.drop_column('products', 'approved_by')
    op.drop_column('products', 'approval_status')
    
    op.drop_column('cases', 'problem_category')
    op.drop_column('cases', 'affected_area_acres')
    op.drop_column('cases', 'crop_stage')
    op.drop_column('cases', 'crop_name')
    
    # Drop new tables (in reverse order of creation)
    op.drop_table('call_metrics')
    op.drop_table('call_summaries')
    op.drop_table('expert_actions')
    op.drop_table('confidence_rules')
    op.drop_table('call_transcripts')
    op.drop_table('advisories')
    op.drop_table('rag_contexts')
    op.drop_table('case_symptoms')
    op.drop_table('problem_symptoms')
    op.drop_table('farmer_profile_responses')
    op.drop_table('farmer_profile_questions')
    op.drop_table('call_states')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS call_outcome_enum')
    op.execute('DROP TYPE IF EXISTS expert_action_enum')
    op.execute('DROP TYPE IF EXISTS speaker_enum')
    op.execute('DROP TYPE IF EXISTS approval_status_enum')
    op.execute('DROP TYPE IF EXISTS call_direction_enum')
    op.execute('DROP TYPE IF EXISTS call_state_enum')
