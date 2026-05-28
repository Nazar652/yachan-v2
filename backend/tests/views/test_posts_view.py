from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import RateLimitedError
from src.schemas.post import PostCreate, PostEditCreate, PostEditResponse, PostResponse
from src.views.posts_view import PostsView
from tests.views._factories import post_ns, request_ns, settings_ns


def build(*, allowed=True):
    post_service = MagicMock()
    post_service.create_reply = AsyncMock(return_value=post_ns())
    post_service.edit_post = AsyncMock(return_value=post_ns(is_edited=True))
    post_service.get_post_history = AsyncMock(return_value=None)
    captcha_service = MagicMock()
    captcha_service.validate = AsyncMock()
    rate_limiter = MagicMock()
    rate_limiter.is_allowed = AsyncMock(return_value=allowed)
    view = PostsView(
        post_service=post_service,
        captcha_service=captcha_service,
        rate_limiter=rate_limiter,
        settings=settings_ns(),
    )
    return view, SimpleNamespace(
        post_service=post_service,
        captcha_service=captcha_service,
        rate_limiter=rate_limiter,
    )


async def test_create_reply_validates_captcha_and_delegates():
    view, mocks = build()
    result = await view.create_reply(
        "b", 5, PostCreate(body="hi"), request_ns(), "tok", "ans"
    )
    assert isinstance(result, PostResponse)
    mocks.captcha_service.validate.assert_awaited_once_with("tok", "ans")
    mocks.post_service.create_reply.assert_awaited_once()


async def test_create_reply_rate_limited():
    view, mocks = build(allowed=False)
    with pytest.raises(RateLimitedError):
        await view.create_reply("b", 5, PostCreate(), request_ns(), "tok", "ans")
    mocks.post_service.create_reply.assert_not_called()


async def test_edit_post_delegates_with_ip_hash():
    view, mocks = build()
    result = await view.edit_post("b", 1, PostEditCreate(new_body="x"), request_ns())
    assert isinstance(result, PostResponse)
    mocks.post_service.edit_post.assert_awaited_once()


async def test_get_post_history_none():
    view, _ = build()
    assert await view.get_post_history("b", 1) is None


async def test_get_post_history_returns_response():
    view, mocks = build()
    mocks.post_service.get_post_history = AsyncMock(
        return_value=SimpleNamespace(
            post_id=1,
            original_body="o",
            original_body_html="<p>o</p>",
            edited_at=datetime(2026, 1, 1),
        )
    )
    result = await view.get_post_history("b", 1)
    assert isinstance(result, PostEditResponse)
