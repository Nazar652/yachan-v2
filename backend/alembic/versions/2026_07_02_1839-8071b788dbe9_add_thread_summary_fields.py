"""add thread summary fields

Revision ID: 8071b788dbe9
Revises: 5ef1b2610cd1
Create Date: 2026-07-02 18:39:02.851955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '8071b788dbe9'
down_revision: Union[str, Sequence[str], None] = '5ef1b2610cd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('thread', sa.Column('summary', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('thread', sa.Column('summary_updated_at', sa.DateTime(timezone=True), nullable=True))
    # not-null on an existing table: default existing rows to 0, then drop the default
    op.add_column(
        'thread',
        sa.Column('summary_post_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.alter_column('thread', 'summary_post_count', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('thread', 'summary_post_count')
    op.drop_column('thread', 'summary_updated_at')
    op.drop_column('thread', 'summary')
