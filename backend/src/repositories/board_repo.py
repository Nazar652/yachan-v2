from kink import inject
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.board import Board
from src.utils.sequences import post_number_sequence_name

from .base import BaseRepository


class BoardRepository(BaseRepository):
    @inject
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, board_id: int) -> Board | None:
        result = await self.session.execute(select(Board).where(col(Board.id) == board_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Board | None:
        result = await self.session.execute(select(Board).where(col(Board.slug) == slug))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Board]:
        result = await self.session.execute(
            select(Board).order_by(col(Board.position).asc(), col(Board.slug).asc())
        )
        return list(result.scalars().all())

    async def create(self, board: Board) -> Board:
        self.session.add(board)
        await self.session.flush()
        await self.session.refresh(board)
        return board

    async def update(self, board: Board) -> Board:
        self.session.add(board)
        await self.session.flush()
        await self.session.refresh(board)
        return board

    async def create_post_number_sequence(self, slug: str) -> None:
        seq = post_number_sequence_name(slug)
        await self.session.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq}"))

    async def drop_post_number_sequence(self, slug: str) -> None:
        seq = post_number_sequence_name(slug)
        await self.session.execute(text(f"DROP SEQUENCE IF EXISTS {seq}"))
