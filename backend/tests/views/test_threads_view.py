from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import src.views.uploads as uploads_module
from src.core.exceptions import RateLimitedError
from src.schemas.thread import ThreadCreate, ThreadDetailResponse, ThreadResponse
from src.views.threads_view import ThreadsView
from tests.views._factories import (
    attachment_ns,
    post_ns,
    request_ns,
    settings_ns,
    thread_ns,
    upload_ns,
)


def build(*, allowed=True, replies=None):
    thread_service = MagicMock()
    thread_service.list_threads = AsyncMock(
        return_value=[
            (
                thread_ns(),
                post_ns(id=10, is_op=True, thread_id=5),
                attachment_ns(thumbnail_path="t.jpg"),
                replies if replies is not None else [],
            )
        ]
    )
    thread_service.get_thread_detail = AsyncMock(
        return_value=(thread_ns(), [post_ns(id=10)], {10: [attachment_ns()]})
    )
    thread_service.create_thread = AsyncMock(return_value=(thread_ns(), post_ns(id=10, is_op=True)))
    file_service = MagicMock()
    file_service.store_attachment = AsyncMock(return_value=attachment_ns())
    captcha_service = MagicMock()
    captcha_service.validate = AsyncMock()
    rate_limiter = MagicMock()
    rate_limiter.is_allowed = AsyncMock(return_value=allowed)
    events = MagicMock()
    events.publish = AsyncMock()
    storage = MagicMock()
    storage.public_url = MagicMock(side_effect=lambda key: f"/media/{key}")
    view = ThreadsView(
        thread_service=thread_service,
        file_service=file_service,
        captcha_service=captcha_service,
        rate_limiter=rate_limiter,
        events=events,
        storage=storage,
        settings=settings_ns(),
    )
    return view, SimpleNamespace(
        thread_service=thread_service,
        file_service=file_service,
        captcha_service=captcha_service,
        rate_limiter=rate_limiter,
        events=events,
    )


async def test_list_threads_maps_responses():
    view, _ = build()
    result = await view.list_threads("b")
    assert all(isinstance(item, ThreadResponse) for item in result)
    assert result[0].op_post is not None
    assert result[0].op_post.body == "hi"
    assert result[0].op_post.thumbnail_url == "/media/t.jpg"
    assert result[0].last_replies == []


async def test_list_threads_maps_last_replies():
    reply = post_ns(id=77, body="reply body", created_at=datetime(2024, 6, 1))
    view, _ = build(replies=[reply])
    result = await view.list_threads("b")
    assert len(result[0].last_replies) == 1
    assert result[0].last_replies[0].id == 77
    assert result[0].last_replies[0].body == "reply body"


async def test_get_thread_includes_posts_with_attachments():
    view, _ = build()
    detail = await view.get_thread("b", 5)
    assert isinstance(detail, ThreadDetailResponse)
    assert len(detail.posts) == 1
    assert len(detail.posts[0].attachments) == 1


async def test_create_thread_with_image_delegates(monkeypatch):
    monkeypatch.setattr(uploads_module, "process_attachment", SimpleNamespace(delay=MagicMock()))
    view, mocks = build()

    result = await view.create_thread(
        "b", ThreadCreate(body="hi"), [upload_ns()], request_ns(), "tok", "ans"
    )

    assert isinstance(result, ThreadDetailResponse)
    assert len(result.posts) == 1
    mocks.captcha_service.validate.assert_awaited_once_with("tok", "ans")
    mocks.thread_service.create_thread.assert_awaited_once()
    # has_image computed from uploads and passed to the service
    assert mocks.thread_service.create_thread.await_args.kwargs["has_image"] is True
    mocks.file_service.store_attachment.assert_awaited_once()
    mocks.events.publish.assert_awaited_once()


async def test_create_thread_rate_limited():
    view, mocks = build(allowed=False)
    with pytest.raises(RateLimitedError):
        await view.create_thread("b", ThreadCreate(), [upload_ns()], request_ns(), "tok", "ans")
    mocks.thread_service.create_thread.assert_not_called()
