"""Add address fields to organisation and company models

Revision ID: ac1c1e5caf25
Revises: 20260225_remove_operator_role
Create Date: 2026-02-26 11:03:36.359456
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ac1c1e5caf25"
down_revision: Union[str, Sequence[str], None] = "20260225_remove_operator_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade() -> None:
    """
    Safe, additive migration only.

    Previous auto-generated migration attempted destructive drops. This migration
    intentionally keeps existing tables/data and only adds missing address columns.
    """
    # Organisations address fields.
    if not _has_column("organisations", "secondary_phone"):
        op.add_column("organisations", sa.Column("secondary_phone", sa.String(length=20), nullable=True))
    if not _has_column("organisations", "address"):
        op.add_column("organisations", sa.Column("address", sa.Text(), nullable=True))
    if not _has_column("organisations", "city"):
        op.add_column("organisations", sa.Column("city", sa.String(length=100), nullable=True))
    if not _has_column("organisations", "state"):
        op.add_column("organisations", sa.Column("state", sa.String(length=100), nullable=True))
    if not _has_column("organisations", "pincode"):
        op.add_column("organisations", sa.Column("pincode", sa.String(length=10), nullable=True))

    # Companies address fields.
    if not _has_column("companies", "secondary_phone"):
        op.add_column("companies", sa.Column("secondary_phone", sa.String(length=20), nullable=True))
    if not _has_column("companies", "city"):
        op.add_column("companies", sa.Column("city", sa.String(length=100), nullable=True))
    if not _has_column("companies", "state"):
        op.add_column("companies", sa.Column("state", sa.String(length=100), nullable=True))
    if not _has_column("companies", "pincode"):
        op.add_column("companies", sa.Column("pincode", sa.String(length=10), nullable=True))


def downgrade() -> None:
    # Reverse additive columns only.
    if _has_column("companies", "pincode"):
        op.drop_column("companies", "pincode")
    if _has_column("companies", "state"):
        op.drop_column("companies", "state")
    if _has_column("companies", "city"):
        op.drop_column("companies", "city")
    if _has_column("companies", "secondary_phone"):
        op.drop_column("companies", "secondary_phone")

    if _has_column("organisations", "pincode"):
        op.drop_column("organisations", "pincode")
    if _has_column("organisations", "state"):
        op.drop_column("organisations", "state")
    if _has_column("organisations", "city"):
        op.drop_column("organisations", "city")
    if _has_column("organisations", "address"):
        op.drop_column("organisations", "address")
    if _has_column("organisations", "secondary_phone"):
        op.drop_column("organisations", "secondary_phone")
