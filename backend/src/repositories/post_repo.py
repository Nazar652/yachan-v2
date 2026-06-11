from kink import inject
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.post import Post
from src.utils.sequences import post_number_sequence_name

from .base import BaseRepository


class PostRepository(BaseRepository):
    @inject
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, post_id: int) -> Post | None:
        result = await self.session.execute(select(Post).where(col(Post.id) == post_id))
        return result.scalar_one_or_none()

    async def get_by_board_and_number(self, board_id: int, post_number: int) -> Post | None:
        result = await self.session.execute(
            select(Post).where(
                col(Post.board_id) == board_id,
                col(Post.post_number) == post_number,
                col(Post.deleted).is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_op_posts_by_thread_ids(self, thread_ids: list[int]) -> dict[int, Post]:
        if not thread_ids:
            return {}
        result = await self.session.execute(
            select(Post).where(
                col(Post.thread_id).in_(thread_ids),
                col(Post.is_op).is_(True),
                col(Post.deleted).is_(False),
            )
        )
        return {post.thread_id: post for post in result.scalars().all()}

    async def get_last_replies_by_thread_ids(
        self, thread_ids: list[int], limit_per_thread: int = 4
    ) -> dict[int, list[Post]]:
        if not thread_ids:
            return {}

        row_number = func.row_number().over(
            partition_by=col(Post.thread_id),
            order_by=col(Post.created_at).desc(),
        ).label("rn")

        ranked_cte = (
            select(col(Post.id), col(Post.thread_id), row_number)
            .where(
                col(Post.thread_id).in_(thread_ids),
                col(Post.is_op).is_(False),
                col(Post.deleted).is_(False),
            )
            .cte("ranked_replies")
        )

        result = await self.session.execute(
            select(Post)
            .join(ranked_cte, col(Post.id) == ranked_cte.c.id)
            .where(ranked_cte.c.rn <= limit_per_thread)
            .order_by(col(Post.thread_id), col(Post.created_at))
        )

        replies: dict[int, list[Post]] = {}
        for post in result.scalars().all():
            replies.setdefault(post.thread_id, []).append(post)

        return replies

    async def count_replies(self, thread_id: int) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Post)
            .where(
                col(Post.thread_id) == thread_id,
                col(Post.is_op).is_(False),
                col(Post.deleted).is_(False),
            )
        )
        return result.scalar_one()

    async def count_by_board(self) -> dict[int, int]:
        result = await self.session.execute(
            select(col(Post.board_id), func.count())
            .where(col(Post.deleted).is_(False))
            .group_by(col(Post.board_id))
        )
        return {board_id: count for board_id, count in result.all()}

    async def get_thread_posts(self, thread_id: int) -> list[Post]:
        result = await self.session.execute(
            select(Post)
            .where(col(Post.thread_id) == thread_id, col(Post.deleted).is_(False))
            .order_by(col(Post.created_at).asc())
        )
        return list(result.scalars().all())

    async def next_post_number(self, board_slug: str) -> int:
        """Atomically advance the per-board sequence and return the next value."""
        seq = post_number_sequence_name(board_slug)
        result = await self.session.execute(text(f"SELECT nextval('{seq}')"))
        return result.scalar_one()

    async def create(self, post: Post) -> Post:
        self.session.add(post)
        await self.session.flush()
        await self.session.refresh(post)
        return post

    async def mark_edited(
        self, post_id: int, new_body: str | None, new_body_html: str | None
    ) -> Post:
        await self.session.execute(
            update(Post)
            .where(col(Post.id) == post_id)
            .values(
                body=new_body,
                body_html=new_body_html,
                is_edited=True,
                edited_at=func.now(),
            )
        )
        await self.session.flush()
        result = await self.session.execute(select(Post).where(col(Post.id) == post_id))
        return result.scalar_one()

    async def soft_delete(self, post_id: int, deleted_by: int | None = None) -> None:
        await self.session.execute(
            update(Post)
            .where(col(Post.id) == post_id)
            .values(deleted=True, deleted_by=deleted_by)
        )
