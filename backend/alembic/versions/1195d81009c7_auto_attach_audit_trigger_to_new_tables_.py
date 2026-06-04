"""auto-attach audit trigger to new tables via event trigger

Revision ID: 1195d81009c7
Revises: 0c9f967591bb
Create Date: 2026-06-04 18:46:09.916319

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1195d81009c7'
down_revision: Union[str, Sequence[str], None] = '0c9f967591bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # event trigger: whenever a CREATE TABLE runs (e.g. a future op.create_table),
    # automatically attach the audit_log_changes() row trigger to the new table,
    # so adding a table can't silently skip auditing. excludes audit_log (would
    # recurse) and alembic_version. note: creating an event trigger needs a
    # superuser role on the database.
    op.execute(
        """
        CREATE FUNCTION audit_attach_to_new_tables() RETURNS event_trigger AS $$
        DECLARE
            command record;
            table_name text;
        BEGIN
            FOR command IN
                SELECT * FROM pg_event_trigger_ddl_commands()
                WHERE object_type = 'table' AND schema_name = 'public'
            LOOP
                SELECT relname INTO table_name FROM pg_class WHERE oid = command.objid;
                IF table_name IN ('audit_log', 'alembic_version') THEN
                    CONTINUE;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM pg_trigger
                    WHERE tgrelid = command.objid AND tgname = 'audit_' || table_name
                ) THEN
                    EXECUTE format(
                        'CREATE TRIGGER %I AFTER INSERT OR UPDATE OR DELETE ON %s '
                        'FOR EACH ROW EXECUTE FUNCTION audit_log_changes()',
                        'audit_' || table_name, command.objid::regclass
                    );
                END IF;
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        "CREATE EVENT TRIGGER audit_new_tables ON ddl_command_end "
        "WHEN TAG IN ('CREATE TABLE') EXECUTE FUNCTION audit_attach_to_new_tables()"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EVENT TRIGGER IF EXISTS audit_new_tables")
    op.execute("DROP FUNCTION IF EXISTS audit_attach_to_new_tables()")
