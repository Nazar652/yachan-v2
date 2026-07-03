from fastapi import APIRouter, Depends

from src.bootstrap.container import get_dependency
from src.schemas.board import BoardCreate, BoardReorder, BoardResponse, BoardUpdate
from src.schemas.mod import BanCreate, BanResponse, ModLogin, TokenResponse
from src.schemas.report import ReportResponse
from src.views.dependencies import bearer_token
from src.views.mod_view import ModView

router = APIRouter(prefix="/mod", tags=["mod"])


@router.post("/login", response_model=TokenResponse)
async def login(data: ModLogin, view: ModView = Depends(lambda: get_dependency(ModView))) -> TokenResponse:
    return await view.login(data)


@router.post("/boards", response_model=BoardResponse, status_code=201)
async def create_board(
    data: BoardCreate,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> BoardResponse:
    return await view.create_board(token, data)


@router.put("/boards/order", response_model=list[BoardResponse])
async def reorder_boards(
    data: BoardReorder,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> list[BoardResponse]:
    return await view.reorder_boards(token, data)


@router.patch("/boards/{board_slug}", response_model=BoardResponse)
async def update_board(
    board_slug: str,
    data: BoardUpdate,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> BoardResponse:
    return await view.update_board(token, board_slug, data)


@router.delete("/{board_slug}/posts/{post_number}", status_code=204)
async def delete_post(
    board_slug: str,
    post_number: int,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> None:
    await view.delete_post(token, board_slug, post_number)


@router.delete("/{board_slug}/threads/{thread_id}", status_code=204)
async def delete_thread(
    board_slug: str,
    thread_id: int,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> None:
    await view.delete_thread(token, board_slug, thread_id)


@router.post("/{board_slug}/threads/{thread_id}/lock", status_code=204)
async def lock_thread(
    board_slug: str,
    thread_id: int,
    locked: bool = True,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> None:
    await view.set_thread_locked(token, board_slug, thread_id, locked)


@router.post("/{board_slug}/threads/{thread_id}/sticky", status_code=204)
async def sticky_thread(
    board_slug: str,
    thread_id: int,
    sticky: bool = True,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> None:
    await view.set_thread_sticky(token, board_slug, thread_id, sticky)


@router.post("/{board_slug}/threads/{thread_id}/summary", status_code=204)
async def regenerate_summary(
    board_slug: str,
    thread_id: int,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> None:
    await view.regenerate_summary(token, board_slug, thread_id)


@router.post("/{board_slug}/posts/{post_number}/ban", response_model=BanResponse, status_code=201)
async def ban_poster(
    board_slug: str,
    post_number: int,
    data: BanCreate,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> BanResponse:
    return await view.ban_poster(token, board_slug, post_number, data)


@router.get("/reports", response_model=list[ReportResponse])
async def list_reports(
    board_id: int | None = None,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> list[ReportResponse]:
    return await view.list_reports(token, board_id)


@router.post("/reports/{report_id}/resolve", status_code=204)
async def resolve_report(
    report_id: int,
    token: str = Depends(bearer_token),
    view: ModView = Depends(lambda: get_dependency(ModView)),
) -> None:
    await view.resolve_report(token, report_id)
