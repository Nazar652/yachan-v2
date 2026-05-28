from fastapi import APIRouter, Depends, Header, Request

from src.schemas.post import PostCreate, PostEditCreate, PostEditResponse, PostResponse
from src.views.posts_view import PostsView

router = APIRouter(prefix="/{board_slug}", tags=["posts"])


def _view() -> PostsView:
    return PostsView()


@router.post("/threads/{thread_id}/posts", response_model=PostResponse, status_code=201)
async def create_reply(
    board_slug: str,
    thread_id: int,
    data: PostCreate,
    request: Request,
    captcha_token: str = Header(alias="X-Captcha-Token"),
    captcha_answer: str = Header(alias="X-Captcha-Answer"),
    view: PostsView = Depends(_view),
) -> PostResponse:
    return await view.create_reply(
        board_slug, thread_id, data, request, captcha_token, captcha_answer
    )


@router.patch("/posts/{post_number}", response_model=PostResponse)
async def edit_post(
    board_slug: str,
    post_number: int,
    data: PostEditCreate,
    request: Request,
    view: PostsView = Depends(_view),
) -> PostResponse:
    return await view.edit_post(board_slug, post_number, data, request)


@router.get("/posts/{post_number}/history", response_model=PostEditResponse | None)
async def get_post_history(
    board_slug: str, post_number: int, view: PostsView = Depends(_view)
) -> PostEditResponse | None:
    return await view.get_post_history(board_slug, post_number)
