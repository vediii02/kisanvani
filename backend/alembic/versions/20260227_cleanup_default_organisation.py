"""Cleanup legacy default organisation if unused.

Revision ID: 20260227_cleanup_default_org
Revises: 20260227_add_org_knowledge_entries
Create Date: 2026-02-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260227_cleanup_default_org"
down_revision: Union[str, Sequence[str], None] = "20260227_add_org_knowledge_entries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return column_name in {c["name"] for c in _inspector().get_columns(table_name)}


def _count_org_refs(table_name: str, org_id: int) -> int:
    if not _has_column(table_name, "organisation_id"):
        return 0
    return op.get_bind().execute(
        sa.text(f"SELECT COUNT(*) FROM {table_name} WHERE organisation_id = :org_id"),
        {"org_id": org_id},
    ).scalar() or 0


def upgrade() -> None:
    if not _has_table("organisations"):
        return

    row = op.get_bind().execute(
        sa.text(
            """
            SELECT id
            FROM organisations
            WHERE domain = 'default.kisanvani.ai'
               OR name = 'Default Organisation'
            ORDER BY id
            LIMIT 1
            """
        )
    ).fetchone()

    if not row:
        return

    default_org_id = int(row[0])
    dependent_tables = [
        "users",
        "farmers",
        "call_sessions",
        "cases",
        "kb_entries",
        "escalations",
        "brands",
        "products",
        "companies",
        "organisation_phone_numbers",
        "organisation_settings",
        "knowledge_entries",
    ]

    total_refs = sum(_count_org_refs(table, default_org_id) for table in dependent_tables)
    if total_refs == 0:
        op.execute(
            sa.text("DELETE FROM organisations WHERE id = :org_id"),
            {"org_id": default_org_id},
        )


def downgrade() -> None:
    # No-op: do not recreate legacy default org automatically.
    pass

