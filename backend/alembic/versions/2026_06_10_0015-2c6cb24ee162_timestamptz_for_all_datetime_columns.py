"""timestamptz for all datetime columns

Revision ID: 2c6cb24ee162
Revises: 1195d81009c7
Create Date: 2026-06-10 00:15:29.968051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '2c6cb24ee162'
down_revision: Union[str, Sequence[str], None] = '1195d81009c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# every timestamp column in the schema, grouped by table. existing naive values
# were written as utc, so they are reinterpreted with `AT TIME ZONE 'UTC'`.
TIMESTAMP_COLUMNS: list[tuple[str, str]] = [
    ("attachment", "created_at"),
    ("attachment", "updated_at"),
    ("ban", "created_at"),
    ("ban", "updated_at"),
    ("ban", "expires_at"),
    ("board", "created_at"),
    ("board", "updated_at"),
    ("mod_account", "created_at"),
    ("mod_account", "updated_at"),
    ("post", "created_at"),
    ("post", "updated_at"),
    ("post", "edited_at"),
    ("post_backlink", "created_at"),
    ("post_backlink", "updated_at"),
    ("post_edit", "created_at"),
    ("post_edit", "updated_at"),
    ("post_edit", "edited_at"),
    ("report", "created_at"),
    ("report", "updated_at"),
    ("thread", "created_at"),
    ("thread", "updated_at"),
    ("thread", "bump_at"),
    ("audit_log", "at"),
]

_AUDIT_FUNCTION_UTC_INSTANT = """
    CREATE OR REPLACE FUNCTION audit_log_changes() RETURNS trigger AS $$
    BEGIN
        INSERT INTO audit_log (table_name, op, row_data, old_data, txid, at)
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            to_jsonb(CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END),
            CASE WHEN TG_OP = 'UPDATE' THEN to_jsonb(OLD) END,
            txid_current(),
            now()
        );
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
"""

_AUDIT_FUNCTION_NAIVE_UTC = """
    CREATE OR REPLACE FUNCTION audit_log_changes() RETURNS trigger AS $$
    BEGIN
        INSERT INTO audit_log (table_name, op, row_data, old_data, txid, at)
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            to_jsonb(CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END),
            CASE WHEN TG_OP = 'UPDATE' THEN to_jsonb(OLD) END,
            txid_current(),
            now() AT TIME ZONE 'utc'
        );
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    """Upgrade schema."""
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
    # the trigger now stores the true instant; the timestamptz column keeps it utc
    op.execute(_AUDIT_FUNCTION_UTC_INSTANT)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(_AUDIT_FUNCTION_NAIVE_UTC)
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=False),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
