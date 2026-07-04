from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, Request, UploadFile

from src.bootstrap.container import get_dependency
from src.schemas.post import PostCreate, PostEditCreate, PostEditResponse, PostResponse
from src.views.dependencies import optional_bearer_token
from src.views.posts_view import PostsView

router = APIRouter(prefix="/{board_slug}", tags=["posts"])


def post_create_from_form(
    name: Annotated[str | None, Form()] = None,
    body: Annotated[str | None, Form()] = None,
    sage: Annotated[bool, Form()] = False,
) -> PostCreate:
    return PostCreate(name=name, body=body, sage=sage)


@router.post("/threads/{thread_id}/posts", response_model=PostResponse, status_code=201)
async def create_reply(
    board_slug: str,
    thread_id: int,
    request: Request,
    data: Annotated[PostCreate, Depends(post_create_from_form)],
    files: list[UploadFile] = File(default=[]),
    captcha_token: str | None = Header(alias="X-Captcha-Token", default=None),
    captcha_answer: str | None = Header(alias="X-Captcha-Answer", default=None),
    admin_token: str | None = Depends(optional_bearer_token),
    view: PostsView = Depends(lambda: get_dependency(PostsView)),
) -> PostResponse:
    return await view.create_reply(
        board_slug, thread_id, data, files, request, captcha_token, captcha_answer, admin_token
    )


@router.patch("/posts/{post_number}", response_model=PostResponse)
async def edit_post(
    board_slug: str,
    post_number: int,
    data: PostEditCreate,
    request: Request,
    view: PostsView = Depends(lambda: get_dependency(PostsView)),
) -> PostResponse:
    return await view.edit_post(board_slug, post_number, data, request)


@router.get("/posts/{post_number}/history", response_model=PostEditResponse | None)
async def get_post_history(
    board_slug: str, post_number: int, view: PostsView = Depends(lambda: get_dependency(PostsView))
) -> PostEditResponse | None:
    return await view.get_post_history(board_slug, post_number)
