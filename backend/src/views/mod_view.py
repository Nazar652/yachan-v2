from kink import inject

from src.core.exceptions import ForbiddenError
from src.models.mod_account import ModAccount, ModRole
from src.schemas.board import BoardCreate, BoardReorder, BoardResponse, BoardUpdate
from src.schemas.mod import BanCreate, BanResponse, ModLogin, TokenResponse
from src.schemas.report import ReportResponse
from src.services.board_service import BoardService
from src.services.mod_service import ModService
from src.services.report_service import ReportService


@inject
class ModView:
    def __init__(
        self,
        mod_service: ModService,
        board_service: BoardService,
        report_service: ReportService,
    ) -> None:
        self.mod_service = mod_service
        self.board_service = board_service
        self.report_service = report_service

    async def login(self, data: ModLogin) -> TokenResponse:
        token, role = await self.mod_service.authenticate(data.username, data.password)
        return TokenResponse(access_token=token, role=role)

    async def create_board(self, token: str, data: BoardCreate) -> BoardResponse:
        mod = await self.mod_service.resolve_mod(token)
        self._require_admin(mod)
        board = await self.board_service.create_board(data)
        return BoardResponse.model_validate(board)

    async def update_board(
        self, token: str, board_slug: str, data: BoardUpdate
    ) -> BoardResponse:
        mod = await self.mod_service.resolve_mod(token)
        self._require_admin(mod)
        board = await self.board_service.update_board(board_slug, data)
        return BoardResponse.model_validate(board)

    async def reorder_boards(self, token: str, data: BoardReorder) -> list[BoardResponse]:
        mod = await self.mod_service.resolve_mod(token)
        self._require_admin(mod)
        boards = await self.board_service.reorder_boards(data.slugs)
        return [BoardResponse.model_validate(board) for board in boards]

    async def delete_post(self, token: str, board_slug: str, post_number: int) -> None:
        mod = await self.mod_service.resolve_mod(token)
        await self.mod_service.delete_post(board_slug, post_number, mod)

    async def set_thread_locked(
        self, token: str, board_slug: str, thread_id: int, locked: bool
    ) -> None:
        await self.mod_service.resolve_mod(token)
        await self.mod_service.set_thread_locked(board_slug, thread_id, locked)

    async def set_thread_sticky(
        self, token: str, board_slug: str, thread_id: int, sticky: bool
    ) -> None:
        await self.mod_service.resolve_mod(token)
        await self.mod_service.set_thread_sticky(board_slug, thread_id, sticky)

    async def ban_poster(
        self, token: str, board_slug: str, post_number: int, data: BanCreate
    ) -> BanResponse:
        mod = await self.mod_service.resolve_mod(token)
        ban = await self.mod_service.ban_poster(board_slug, post_number, data, mod)
        return BanResponse.model_validate(ban)

    async def list_reports(
        self, token: str, board_id: int | None = None
    ) -> list[ReportResponse]:
        await self.mod_service.resolve_mod(token)
        reports = await self.report_service.list_unresolved(board_id)
        return [ReportResponse.model_validate(report) for report in reports]

    async def resolve_report(self, token: str, report_id: int) -> None:
        mod = await self.mod_service.resolve_mod(token)
        await self.report_service.resolve(report_id, mod.id)

    @staticmethod
    def _require_admin(mod: ModAccount) -> None:
        if mod.role != ModRole.ADMIN:
            raise ForbiddenError("admin privileges required")
