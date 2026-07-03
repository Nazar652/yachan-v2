"""add post_embedding table with pgvector

Revision ID: 5ef1b2610cd1
Revises: a62e92ad23db
Create Date: 2026-07-02 17:39:34.768412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '5ef1b2610cd1'
down_revision: Union[str, Sequence[str], None] = 'a62e92ad23db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('post_embedding',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.Vector(384), nullable=False),
    sa.ForeignKeyConstraint(['post_id'], ['post.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('post_id')
    )

    # embeddings are large derived data with no audit value; drop the audit
    # trigger the CREATE TABLE event trigger auto-attached, so upserts don't copy
    # a 384-float vector into audit_log on every write.
    op.execute("DROP TRIGGER IF EXISTS audit_post_embedding ON post_embedding")

    # approximate nearest-neighbour index for cosine distance search
    op.execute(
        "CREATE INDEX ix_post_embedding_embedding ON post_embedding "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('post_embedding')
    op.execute("DROP EXTENSION IF EXISTS vector")
