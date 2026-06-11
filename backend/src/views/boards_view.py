from kink import inject
from starlette.requests import Request

from src.core.config import Settings
from src.schemas.board import BoardResponse
from src.services.board_service import BoardService
from src.utils.online import OnlineTracker
from src.views.dependencies import client_ip_hash


class BoardsView:
    @inject
    def __init__(
        self,
        board_service: BoardService,
        online_tracker: OnlineTracker,
        settings: Settings,
    ) -> None:
        self.board_service = board_service
        self.online_tracker = online_tracker
        self.settings = settings

    async def list_boards(self, request: Request) -> list[BoardResponse]:
        await self.online_tracker.touch(client_ip_hash(request, self.settings))
        boards = await self.board_service.list_boards()
        return [BoardResponse.model_validate(board) for board in boards]

    async def get_board(self, slug: str) -> BoardResponse:
        board = await self.board_service.get_board(slug)
        return BoardResponse.model_validate(board)
