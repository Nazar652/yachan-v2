from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, Query, Request, UploadFile

from src.bootstrap.container import get_dependency
from src.schemas.search import SimilarThreadResponse
from src.schemas.thread import ThreadCreate, ThreadDetailResponse, ThreadResponse
from src.views.dependencies import optional_bearer_token
from src.views.search_view import SearchView
from src.views.threads_view import ThreadsView

router = APIRouter(prefix="/{board_slug}/threads", tags=["threads"])


def thread_create_from_form(
    title: Annotated[str | None, Form()] = None,
    name: Annotated[str | None, Form()] = None,
    body: Annotated[str | None, Form()] = None,
    sage: Annotated[bool, Form()] = False,
) -> ThreadCreate:
    return ThreadCreate(title=title, name=name, body=body, sage=sage)


@router.get("", response_model=list[ThreadResponse])
async def list_threads(
    board_slug: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
    view: ThreadsView = Depends(lambda: get_dependency(ThreadsView)),
) -> list[ThreadResponse]:
    return await view.list_threads(board_slug, request, limit, offset)


@router.get("/similar", response_model=list[SimilarThreadResponse])
async def similar_threads_for_text(
    board_slug: str,
    request: Request,
    q: str = Query(min_length=1, max_length=200),
    view: SearchView = Depends(lambda: get_dependency(SearchView)),
) -> list[SimilarThreadResponse]:
    return await view.similar_threads_for_text(board_slug, q, request)


@router.get("/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread(
    board_slug: str,
    thread_id: int,
    request: Request,
    view: ThreadsView = Depends(lambda: get_dependency(ThreadsView)),
) -> ThreadDetailResponse:
    return await view.get_thread(board_slug, thread_id, request)


@router.get("/{thread_id}/similar", response_model=list[SimilarThreadResponse])
async def similar_threads(
    board_slug: str,
    thread_id: int,
    request: Request,
    view: SearchView = Depends(lambda: get_dependency(SearchView)),
) -> list[SimilarThreadResponse]:
    return await view.similar_threads(board_slug, thread_id, request)


@router.post("", response_model=ThreadDetailResponse, status_code=201)
async def create_thread(
    board_slug: str,
    request: Request,
    data: Annotated[ThreadCreate, Depends(thread_create_from_form)],
    files: list[UploadFile] = File(default=[]),
    captcha_token: str | None = Header(alias="X-Captcha-Token", default=None),
    captcha_answer: str | None = Header(alias="X-Captcha-Answer", default=None),
    admin_token: str | None = Depends(optional_bearer_token),
    view: ThreadsView = Depends(lambda: get_dependency(ThreadsView)),
) -> ThreadDetailResponse:
    return await view.create_thread(
        board_slug, data, files, request, captcha_token, captcha_answer, admin_token
    )
