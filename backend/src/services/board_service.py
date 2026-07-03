from kink import inject

from src.core.exceptions import (
    BadRequestError,
    BoardAlreadyExistsError,
    BoardNotFoundError,
)
from src.models.board import Board
from src.repositories.board_repo import BoardRepository
from src.schemas.board import BoardCreate, BoardUpdate


class BoardService:
    @inject
    def __init__(self, board_repo: BoardRepository) -> None:
        self.board_repo = board_repo

    async def create_board(self, data: BoardCreate) -> Board:
        if await self.board_repo.get_by_slug(data.slug) is not None:
            raise BoardAlreadyExistsError(data.slug)

        board = await self.board_repo.create(
            Board(
                slug=data.slug,
                title=data.title,
                description=data.description,
                bump_limit=data.bump_limit,
                is_nsfw=data.is_nsfw,
            )
        )
        # each board owns a sequence that numbers its posts from 1
        await self.board_repo.create_post_number_sequence(board.slug)
        return board

    async def update_board(self, slug: str, data: BoardUpdate) -> Board:
        board = await self.board_repo.get_by_slug(slug)
        if board is None:
            raise BoardNotFoundError(slug)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(board, field, value)
        return await self.board_repo.update(board)

    async def reorder_boards(self, slugs: list[str]) -> list[Board]:
        boards = await self.board_repo.list_all()
        by_slug = {board.slug: board for board in boards}

        if len(slugs) != len(by_slug) or set(slugs) != set(by_slug):
            raise BadRequestError("slugs must list every existing board exactly once")

        reordered: list[Board] = []
        for index, slug in enumerate(slugs):
            board = by_slug[slug]
            board.position = index
            reordered.append(await self.board_repo.update(board))

        return reordered

    async def list_boards(self) -> list[Board]:
        return await self.board_repo.list_all()

    async def get_board(self, slug: str) -> Board:
        board = await self.board_repo.get_by_slug(slug)
        if board is None:
            raise BoardNotFoundError(slug)
        return board
