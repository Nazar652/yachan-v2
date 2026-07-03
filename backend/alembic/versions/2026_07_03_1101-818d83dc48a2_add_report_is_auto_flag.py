"""add report is_auto flag

Revision ID: 818d83dc48a2
Revises: 8071b788dbe9
Create Date: 2026-07-03 11:01:13.115768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '818d83dc48a2'
down_revision: Union[str, Sequence[str], None] = '8071b788dbe9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default false backfills existing reports (all human-filed), then dropped;
    # the app sets is_auto explicitly (model default false)
    op.add_column('report', sa.Column('is_auto', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column('report', 'is_auto', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('report', 'is_auto')
