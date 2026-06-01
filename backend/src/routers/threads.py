from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, Request, UploadFile

from src.schemas.thread import ThreadCreate, ThreadDetailResponse, ThreadResponse
from src.views.threads_view import ThreadsView

router = APIRouter(prefix="/{board_slug}/threads", tags=["threads"])


def _view() -> ThreadsView:
    return ThreadsView()


@router.get("", response_model=list[ThreadResponse])
async def list_threads(
    board_slug: str,
    limit: int = 50,
    offset: int = 0,
    view: ThreadsView = Depends(_view),
) -> list[ThreadResponse]:
    return await view.list_threads(board_slug, limit, offset)


@router.get("/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread(
    board_slug: str, thread_id: int, view: ThreadsView = Depends(_view)
) -> ThreadDetailResponse:
    return await view.get_thread(board_slug, thread_id)


@router.post("", response_model=ThreadDetailResponse, status_code=201)
async def create_thread(
    board_slug: str,
    request: Request,
    data: Annotated[ThreadCreate, Form()],
    files: list[UploadFile] = File(default=[]),
    captcha_token: str = Header(alias="X-Captcha-Token"),
    captcha_answer: str = Header(alias="X-Captcha-Answer"),
    view: ThreadsView = Depends(_view),
) -> ThreadDetailResponse:
    return await view.create_thread(
        board_slug, data, files, request, captcha_token, captcha_answer
    )
