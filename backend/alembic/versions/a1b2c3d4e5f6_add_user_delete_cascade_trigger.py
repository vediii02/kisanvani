"""add_user_delete_cascade_trigger

Revision ID: a1b2c3d4e5f6
Revises: 724174dfd41a
Create Date: 2026-03-07 13:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '724174dfd41a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create a PostgreSQL trigger that fires BEFORE DELETE on users table.
    When a user is deleted:
      - If role='organisation' and organisation_id is set → delete that organisation
        (which cascades to its companies, brands, products via existing FK cascades)
      - If role='company' and company_id is set → delete that company
        (which cascades to its brands, products via existing FK cascades)
    
    Only deletes if no OTHER users reference the same org/company.
    """

    # Create the trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_cascade_delete_user_resources()
        RETURNS TRIGGER AS $$
        BEGIN
            -- For organisation role users: delete the organisation if no other users reference it
            IF OLD.role = 'organisation' AND OLD.organisation_id IS NOT NULL THEN
                -- First, set this user's FK to NULL to avoid circular dependency
                -- (the row is being deleted anyway)
                IF NOT EXISTS (
                    SELECT 1 FROM users 
                    WHERE organisation_id = OLD.organisation_id 
                    AND id != OLD.id
                ) THEN
                    DELETE FROM organisations WHERE id = OLD.organisation_id;
                END IF;
            END IF;

            -- For company role users: delete the company if no other users reference it
            IF OLD.role = 'company' AND OLD.company_id IS NOT NULL THEN
                IF NOT EXISTS (
                    SELECT 1 FROM users 
                    WHERE company_id = OLD.company_id 
                    AND id != OLD.id
                ) THEN
                    DELETE FROM companies WHERE id = OLD.company_id;
                END IF;
            END IF;

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create the trigger (BEFORE DELETE so the user row still exists for the check)
    op.execute("""
        CREATE TRIGGER trg_cascade_delete_user_resources
        BEFORE DELETE ON users
        FOR EACH ROW
        EXECUTE FUNCTION fn_cascade_delete_user_resources();
    """)


def downgrade() -> None:
    """Remove the trigger and function."""
    op.execute("DROP TRIGGER IF EXISTS trg_cascade_delete_user_resources ON users;")
    op.execute("DROP FUNCTION IF EXISTS fn_cascade_delete_user_resources();")
