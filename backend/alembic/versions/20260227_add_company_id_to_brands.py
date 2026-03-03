"""Add missing company_id column to brands for ORM parity.

Revision ID: 20260227_add_brand_company_id
Revises: 20260227_cleanup_default_org
Create Date: 2026-02-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260227_add_brand_company_id"
down_revision: Union[str, Sequence[str], None] = "20260227_cleanup_default_org"
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


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return index_name in {i["name"] for i in _inspector().get_indexes(table_name)}


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
    if not _has_table("brands"):
        return

    if not _has_column("brands", "company_id"):
        op.add_column("brands", sa.Column("company_id", sa.Integer(), nullable=True))

    if _has_column("brands", "company_id") and not _has_index("brands", "ix_brands_company_id"):
        op.create_index("ix_brands_company_id", "brands", ["company_id"], unique=False)

    if _has_column("brands", "company_id") and _has_table("companies") and not _has_fk("brands", ("company_id",), "companies"):
        op.create_foreign_key(
            "fk_brands_company_id_companies",
            "brands",
            "companies",
            ["company_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    if not _has_table("brands"):
        return

    if _has_fk("brands", ("company_id",), "companies"):
        op.drop_constraint("fk_brands_company_id_companies", "brands", type_="foreignkey")

    if _has_index("brands", "ix_brands_company_id"):
        op.drop_index("ix_brands_company_id", table_name="brands")

    if _has_column("brands", "company_id"):
        op.drop_column("brands", "company_id")
