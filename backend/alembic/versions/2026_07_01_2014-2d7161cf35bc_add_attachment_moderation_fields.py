"""add attachment moderation fields

Revision ID: 2d7161cf35bc
Revises: 2c6cb24ee162
Create Date: 2026-07-01 20:14:52.469439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '2d7161cf35bc'
down_revision: Union[str, Sequence[str], None] = '2c6cb24ee162'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# native enum with member names as labels, like the existing mediatype/modrole columns;
# add_column does not emit CREATE TYPE, so create/drop it explicitly (create_type=False
# keeps add_column from trying to create it a second time)
moderation_status = sa.Enum(
    'PENDING', 'SAFE', 'FLAGGED', 'BLOCKED', name='moderationstatus', create_type=False
)


def upgrade() -> None:
    """Upgrade schema."""
    moderation_status.create(op.get_bind(), checkfirst=True)
    # server_default 'SAFE' grandfathers existing (already-published) rows into the
    # NOT NULL column, then dropped — the app assigns the status (model default PENDING)
    op.add_column(
        'attachment',
        sa.Column('moderation_status', moderation_status, nullable=False, server_default='SAFE'),
    )
    op.add_column('attachment', sa.Column('nsfw_score', sa.Float(), nullable=True))
    op.create_index(
        op.f('ix_attachment_moderation_status'), 'attachment', ['moderation_status'], unique=False
    )
    op.alter_column('attachment', 'moderation_status', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_attachment_moderation_status'), table_name='attachment')
    op.drop_column('attachment', 'nsfw_score')
    op.drop_column('attachment', 'moderation_status')
    # autogenerate never drops the enum type
    moderation_status.drop(op.get_bind(), checkfirst=True)
