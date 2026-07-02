from kink import inject
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.board import Board
from src.models.post import Post
from src.models.post_embedding import PostEmbedding

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

    async def search(
        self, embedding: list[float], *, board_id: int | None = None, limit: int = 20
    ) -> list[tuple[Post, str, float]]:
        # pgvector's cosine_distance comparator is hidden behind SQLModel's Mapped type
        distance = col(PostEmbedding.embedding).cosine_distance(embedding).label("distance")  # type: ignore[attr-defined]
        query = (
            select(Post, col(Board.slug), distance)
            .join(PostEmbedding, col(Post.id) == col(PostEmbedding.post_id))
            .join(Board, col(Post.board_id) == col(Board.id))
            .where(col(Post.deleted).is_(False))
        )
        if board_id is not None:
            query = query.where(col(Post.board_id) == board_id)
        query = query.order_by(distance).limit(limit)

        result = await self.session.execute(query)
        return [(post, slug, dist) for post, slug, dist in result.all()]
