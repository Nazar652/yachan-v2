from fastapi import APIRouter, Depends, WebSocket

from src.bootstrap.container import get_dependency
from src.views.ws_view import WsView

router = APIRouter(prefix="/{board_slug}", tags=["ws"])


@router.websocket("/threads/{thread_id}/ws")
async def thread_ws(
    websocket: WebSocket,
    thread_id: int,
    view: WsView = Depends(lambda: get_dependency(WsView)),
) -> None:
    await view.thread_feed(websocket, thread_id)


@router.websocket("/ws")
async def board_ws(
    websocket: WebSocket,
    board_slug: str,
    view: WsView = Depends(lambda: get_dependency(WsView)),
) -> None:
    await view.board_feed(websocket, board_slug)
