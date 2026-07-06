from kink import inject
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.board import Board
from src.models.post import Post
from src.models.post_embedding import PostEmbedding
from src.models.thread import Thread

from .base import BaseRepository


class PostEmbeddingRepository(BaseRepository):
    @inject
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def upsert(self, post_id: int, embedding: list[float]) -> None:
        statement = insert(PostEmbedding).values(post_id=post_id, embedding=embedding)
        statement = statement.on_conflict_do_update(
            index_elements=["post_id"],
            set_={"embedding": statement.excluded.embedding, "updated_at": func.now()},
        )
        await self.session.execute(statement)

    async def get_by_post_id(self, post_id: int) -> list[float] | None:
        query = select(col(PostEmbedding.embedding)).where(col(PostEmbedding.post_id) == post_id)
        result = await self.session.execute(query)
        embedding = result.scalar_one_or_none()
        # pgvector deserializes to a numpy array when numpy is installed, a plain
        # list otherwise; normalize to a plain list of python floats either way
        return None if embedding is None else [float(value) for value in embedding]

    async def search(
        self,
        embedding: list[float],
        query_text: str,
        *,
        board_id: int | None = None,
        limit: int = 20,
    ) -> list[tuple[Post, str, float]]:
        # pgvector's cosine_distance comparator is hidden behind SQLModel's Mapped type
        distance = col(PostEmbedding.embedding).cosine_distance(embedding).label("distance")  # type: ignore[attr-defined]
        # lexical tier: the 'simple' config tokenises on whitespace/punctuation without
        # stemming, so it matches exact words in any language (incl. cyrillic)
        lexical = (
            func.to_tsvector("simple", col(Post.body))
            .op("@@")(func.plainto_tsquery("simple", query_text))
            .label("lexical")
        )
        query = (
            select(Post, col(Board.slug), distance)
            .join(PostEmbedding, col(Post.id) == col(PostEmbedding.post_id))
            .join(Board, col(Post.board_id) == col(Board.id))
            .where(col(Post.deleted).is_(False))
        )
        if board_id is not None:
            query = query.where(col(Post.board_id) == board_id)
        # literal keyword matches first, then by semantic closeness within each tier
        query = query.order_by(lexical.desc(), distance).limit(limit)

        result = await self.session.execute(query)
        return [(post, slug, dist) for post, slug, dist in result.all()]

    async def similar_threads(
        self,
        embedding: list[float],
        *,
        exclude_thread_id: int,
        board_id: int | None = None,
        limit: int = 5,
        max_distance: float | None = None,
    ) -> list[tuple[Thread, str, Post, float]]:
        distance = col(PostEmbedding.embedding).cosine_distance(embedding).label("distance")  # type: ignore[attr-defined]
        query = (
            select(Thread, col(Board.slug), Post, distance)
            .join(Post, col(PostEmbedding.post_id) == col(Post.id))
            .join(Thread, col(Post.thread_id) == col(Thread.id))
            .join(Board, col(Thread.board_id) == col(Board.id))
            .where(col(Post.is_op).is_(True))
            .where(col(Post.deleted).is_(False))
            .where(col(Post.thread_id) != exclude_thread_id)
        )
        if board_id is not None:
            query = query.where(col(Thread.board_id) == board_id)
        if max_distance is not None:
            query = query.where(distance < max_distance)
        query = query.order_by(distance).limit(limit)

        result = await self.session.execute(query)
        return [(thread, slug, post, dist) for thread, slug, post, dist in result.all()]
