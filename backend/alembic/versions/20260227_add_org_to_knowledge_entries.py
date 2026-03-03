"""Add organisation_id to knowledge_entries for tenant isolation.

Revision ID: 20260227_add_org_knowledge_entries
Revises: 20260227_schema_repair
Create Date: 2026-02-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260227_add_org_knowledge_entries"
down_revision: Union[str, Sequence[str], None] = "20260227_schema_repair"
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
    if not _has_table("knowledge_entries"):
        return

    org_count = op.get_bind().execute(sa.text("SELECT COUNT(*) FROM organisations")).scalar() or 0
    if org_count == 0:
        raise RuntimeError(
            "Cannot enforce tenant isolation for knowledge_entries: organisations table has no rows."
        )

    if not _has_column("knowledge_entries", "organisation_id"):
        op.add_column("knowledge_entries", sa.Column("organisation_id", sa.Integer(), nullable=True))

    # Backfill existing rows to a default org before enforcing NOT NULL.
    op.execute(
        """
        UPDATE knowledge_entries
        SET organisation_id = (
            SELECT id FROM organisations ORDER BY id ASC LIMIT 1
        )
        WHERE organisation_id IS NULL
        """
    )

    op.alter_column("knowledge_entries", "organisation_id", existing_type=sa.Integer(), nullable=False)

    if not _has_fk("knowledge_entries", ("organisation_id",), "organisations"):
        op.create_foreign_key(
            "fk_knowledge_entries_organisation_id",
            "knowledge_entries",
            "organisations",
            ["organisation_id"],
            ["id"],
            ondelete="CASCADE",
        )

    if not _has_index("knowledge_entries", "ix_knowledge_entries_organisation_id"):
        op.create_index(
            "ix_knowledge_entries_organisation_id",
            "knowledge_entries",
            ["organisation_id"],
            unique=False,
        )


def downgrade() -> None:
    if not _has_table("knowledge_entries"):
        return

    if _has_index("knowledge_entries", "ix_knowledge_entries_organisation_id"):
        op.drop_index("ix_knowledge_entries_organisation_id", table_name="knowledge_entries")

    if _has_fk("knowledge_entries", ("organisation_id",), "organisations"):
        op.drop_constraint("fk_knowledge_entries_organisation_id", "knowledge_entries", type_="foreignkey")

    if _has_column("knowledge_entries", "organisation_id"):
        op.drop_column("knowledge_entries", "organisation_id")
