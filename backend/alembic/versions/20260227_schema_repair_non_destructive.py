"""Non-destructive schema repair for model/runtime compatibility.

Revision ID: 20260227_schema_repair
Revises: 2447e7c785a2
Create Date: 2026-02-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260227_schema_repair"
down_revision: Union[str, Sequence[str], None] = "2447e7c785a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    cols = {c["name"] for c in _inspector().get_columns(table_name)}
    return column_name in cols


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    idx = {i["name"] for i in _inspector().get_indexes(table_name)}
    return index_name in idx


def _has_fk(table_name: str, local_cols: tuple[str, ...], referred_table: str) -> bool:
    if not _has_table(table_name):
        return False
    for fk in _inspector().get_foreign_keys(table_name):
        cols = tuple(fk.get("constrained_columns") or [])
        ref = fk.get("referred_table")
        if cols == local_cols and ref == referred_table:
            return True
    return False


def upgrade() -> None:
    # Restore tables used by superadmin/audit features if missing.
    if not _has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), nullable=True, index=True),
            sa.Column("username", sa.String(100), nullable=False),
            sa.Column("user_role", sa.String(50), nullable=False),
            sa.Column("action_type", sa.String(100), nullable=False, index=True),
            sa.Column("action_category", sa.String(50), nullable=False, index=True),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("entity_type", sa.String(50), nullable=True),
            sa.Column("entity_id", sa.Integer(), nullable=True, index=True),
            sa.Column("organisation_id", sa.Integer(), nullable=True, index=True),
            sa.Column("old_value", sa.JSON(), nullable=True),
            sa.Column("new_value", sa.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.String(255), nullable=True),
            sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
            sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("extra_data", sa.JSON(), nullable=True),
        )

    if not _has_table("platform_config"):
        op.create_table(
            "platform_config",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("ai_confidence_threshold", sa.Integer(), nullable=True, server_default="70"),
            sa.Column("max_call_duration_minutes", sa.Integer(), nullable=True, server_default="15"),
            sa.Column("default_language", sa.String(10), nullable=True, server_default="hi"),
            sa.Column("stt_provider", sa.String(50), nullable=True, server_default="bhashini"),
            sa.Column("tts_provider", sa.String(50), nullable=True, server_default="bhashini"),
            sa.Column("llm_model", sa.String(100), nullable=True, server_default="gpt-4"),
            sa.Column("rag_strictness_level", sa.String(20), nullable=True, server_default="medium"),
            sa.Column("rag_min_confidence", sa.Integer(), nullable=True, server_default="60"),
            sa.Column("rag_max_results", sa.Integer(), nullable=True, server_default="5"),
            sa.Column("force_kb_approval", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("enable_call_recording", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("enable_auto_escalation", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("trial_duration_days", sa.Integer(), nullable=True, server_default="14"),
            sa.Column("max_concurrent_calls", sa.Integer(), nullable=True, server_default="100"),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _has_table("banned_products"):
        op.create_table(
            "banned_products",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("product_name", sa.String(200), nullable=False, index=True),
            sa.Column("chemical_name", sa.String(200), nullable=True),
            sa.Column("ban_reason", sa.Text(), nullable=False),
            sa.Column("regulatory_reference", sa.String(255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("banned_by_user_id", sa.Integer(), nullable=False),
            sa.Column("banned_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("expiry_date", sa.Date(), nullable=True),
            sa.Column("extra_data", sa.JSON(), nullable=True),
        )

    # Organisation model parity.
    if _has_table("organisations"):
        if not _has_column("organisations", "domain"):
            op.add_column("organisations", sa.Column("domain", sa.String(200), nullable=True))
        if not _has_column("organisations", "email"):
            op.add_column("organisations", sa.Column("email", sa.String(200), nullable=True))
        if not _has_column("organisations", "preferred_languages"):
            op.add_column("organisations", sa.Column("preferred_languages", sa.String(100), nullable=True, server_default="hi"))
        if not _has_column("organisations", "greeting_message"):
            op.add_column("organisations", sa.Column("greeting_message", sa.Text(), nullable=True))
        if not _has_index("organisations", "ix_organisations_primary_phone") and _has_column("organisations", "primary_phone"):
            op.create_index("ix_organisations_primary_phone", "organisations", ["primary_phone"], unique=True)

    # Company model parity.
    if _has_table("companies"):
        if not _has_column("companies", "max_operators"):
            op.add_column("companies", sa.Column("max_operators", sa.Integer(), nullable=True, server_default="5"))
        if not _has_column("companies", "max_products"):
            op.add_column("companies", sa.Column("max_products", sa.Integer(), nullable=True, server_default="100"))

    # Critical org scoping columns for call flows.
    if _has_table("farmers") and not _has_column("farmers", "organisation_id"):
        op.add_column("farmers", sa.Column("organisation_id", sa.Integer(), nullable=True))
    if _has_table("cases") and not _has_column("cases", "organisation_id"):
        op.add_column("cases", sa.Column("organisation_id", sa.Integer(), nullable=True))
    if _has_table("escalations") and not _has_column("escalations", "organisation_id"):
        op.add_column("escalations", sa.Column("organisation_id", sa.Integer(), nullable=True))

    if _has_column("farmers", "organisation_id") and not _has_fk("farmers", ("organisation_id",), "organisations"):
        op.create_foreign_key(
            "fk_farmers_organisation_id_repair",
            "farmers",
            "organisations",
            ["organisation_id"],
            ["id"],
            ondelete="CASCADE",
        )
    if _has_column("cases", "organisation_id") and not _has_fk("cases", ("organisation_id",), "organisations"):
        op.create_foreign_key(
            "fk_cases_organisation_id_repair",
            "cases",
            "organisations",
            ["organisation_id"],
            ["id"],
            ondelete="CASCADE",
        )
    if _has_column("escalations", "organisation_id") and not _has_fk("escalations", ("organisation_id",), "organisations"):
        op.create_foreign_key(
            "fk_escalations_organisation_id_repair",
            "escalations",
            "organisations",
            ["organisation_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    # Intentionally minimal: this is a forward-fix repair migration.
    pass
