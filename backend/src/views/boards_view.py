from kink import inject

from src.schemas.board import BoardResponse
from src.services.board_service import BoardService


class BoardsView:
    @inject
    def __init__(self, board_service: BoardService) -> None:
        self.board_service = board_service

    async def list_boards(self) -> list[BoardResponse]:
        boards = await self.board_service.list_boards()
        return [BoardResponse.model_validate(board) for board in boards]

    async def get_board(self, slug: str) -> BoardResponse:
        board = await self.board_service.get_board(slug)
        return BoardResponse.model_validate(board)
