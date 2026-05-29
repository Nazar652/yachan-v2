from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.exceptions import RateLimitedError
from src.schemas.thread import ThreadCreate, ThreadDetailResponse, ThreadResponse
from src.views.threads_view import ThreadsView
from tests.views._factories import post_ns, request_ns, settings_ns, thread_ns


def build(*, allowed=True):
    thread_service = MagicMock()
    thread_service.list_threads = AsyncMock(return_value=[thread_ns()])
    thread_service.get_thread_detail = AsyncMock(return_value=(thread_ns(), [post_ns()]))
    thread_service.create_thread = AsyncMock(return_value=(thread_ns(), post_ns(is_op=True)))
    captcha_service = MagicMock()
    captcha_service.validate = AsyncMock()
    rate_limiter = MagicMock()
    rate_limiter.is_allowed = AsyncMock(return_value=allowed)
    events = MagicMock()
    events.publish = AsyncMock()
    view = ThreadsView(
        thread_service=thread_service,
        captcha_service=captcha_service,
        rate_limiter=rate_limiter,
        events=events,
        settings=settings_ns(),
    )
    return view, SimpleNamespace(
        thread_service=thread_service,
        captcha_service=captcha_service,
        rate_limiter=rate_limiter,
        events=events,
    )


async def test_list_threads_maps_responses():
    view, _ = build()
    result = await view.list_threads("b")
    assert all(isinstance(item, ThreadResponse) for item in result)


async def test_get_thread_includes_posts():
    view, _ = build()
    detail = await view.get_thread("b", 5)
    assert isinstance(detail, ThreadDetailResponse)
    assert len(detail.posts) == 1


async def test_create_thread_validates_captcha_and_delegates():
    view, mocks = build()
    result = await view.create_thread(
        "b", ThreadCreate(body="hi"), request_ns(), "tok", "ans"
    )
    assert isinstance(result, ThreadResponse)
    mocks.captcha_service.validate.assert_awaited_once_with("tok", "ans")
    mocks.thread_service.create_thread.assert_awaited_once()
    mocks.events.publish.assert_awaited_once()


async def test_create_thread_rate_limited():
    view, mocks = build(allowed=False)
    with pytest.raises(RateLimitedError):
        await view.create_thread("b", ThreadCreate(), request_ns(), "tok", "ans")
    mocks.thread_service.create_thread.assert_not_called()
