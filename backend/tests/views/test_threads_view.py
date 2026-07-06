from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import src.views.threads_view as threads_view_module
import src.views.uploads as uploads_module
from src.core.exceptions import BadRequestError, InvalidCaptchaError, RateLimitedError
from src.schemas.thread import ThreadCreate, ThreadDetailResponse, ThreadResponse
from src.utils.clock import utcnow
from src.views.threads_view import ThreadsView
from tests.views._factories import (
    attachment_ns,
    board_ns,
    post_ns,
    request_ns,
    settings_ns,
    thread_ns,
    upload_ns,
)


def build(*, allowed=True, replies=None, op_images=None):
    if op_images is None:
        op_images = [attachment_ns(thumbnail_path="t.jpg")]
    thread_service = MagicMock()
    thread_service.list_threads = AsyncMock(
        return_value=[
            (
                thread_ns(),
                post_ns(id=10, is_op=True, thread_id=5),
                op_images,
                replies if replies is not None else [],
            )
        ]
    )
    thread_service.get_thread_detail = AsyncMock(
        return_value=(thread_ns(), [post_ns(id=10)], {10: [attachment_ns()]})
    )
    thread_service.create_thread = AsyncMock(return_value=(thread_ns(), post_ns(id=10, is_op=True)))
    board_service = MagicMock()
    board_service.get_board = AsyncMock(return_value=board_ns())
    board_service.list_boards = AsyncMock(return_value=[board_ns()])
    file_service = MagicMock()
    file_service.store_attachment = AsyncMock(return_value=attachment_ns())
    captcha_service = MagicMock()
    captcha_service.validate = AsyncMock()
    mod_service = MagicMock()
    mod_service.is_admin = AsyncMock(return_value=False)
    rate_limiter = MagicMock()
    rate_limiter.is_allowed = AsyncMock(return_value=allowed)
    events = MagicMock()
    events.publish = AsyncMock()
    storage = MagicMock()
    storage.public_url = MagicMock(side_effect=lambda key: f"/media/{key}")
    online_tracker = MagicMock()
    online_tracker.touch = AsyncMock()
    view = ThreadsView(
        thread_service=thread_service,
        board_service=board_service,
        file_service=file_service,
        captcha_service=captcha_service,
        mod_service=mod_service,
        rate_limiter=rate_limiter,
        events=events,
        storage=storage,
        settings=settings_ns(),
        online_tracker=online_tracker,
    )
    return view, SimpleNamespace(
        thread_service=thread_service,
        board_service=board_service,
        file_service=file_service,
        captcha_service=captcha_service,
        mod_service=mod_service,
        rate_limiter=rate_limiter,
        events=events,
        online_tracker=online_tracker,
    )


@pytest.fixture(autouse=True)
def embed_delay(monkeypatch):
    delay = MagicMock()
    monkeypatch.setattr(threads_view_module, "embed_post", SimpleNamespace(delay=delay))
    return delay


@pytest.fixture(autouse=True)
def moderate_send_task(monkeypatch):
    send_task = MagicMock()
    monkeypatch.setattr(threads_view_module.celery, "send_task", send_task)
    return send_task


async def test_list_threads_maps_responses():
    view, _ = build()
    result = await view.list_threads("b", request_ns())
    assert all(isinstance(item, ThreadResponse) for item in result)
    assert result[0].op_post is not None
    assert result[0].op_post.body == "hi"
    assert result[0].op_post.body_html == "<p>hi</p>"
    assert result[0].op_post.thumbnail_url == "/media/t.jpg"
    assert result[0].last_replies == []


async def test_list_threads_falls_back_to_full_image_without_thumbnail():
    view, _ = build(op_images=[attachment_ns(thumbnail_path=None, file_path="full.jpg")])
    result = await view.list_threads("b", request_ns())
    assert result[0].op_post is not None
    assert result[0].op_post.thumbnail_url == "/media/full.jpg"


async def test_list_threads_exposes_op_image_dimensions():
    view, _ = build(op_images=[attachment_ns(thumbnail_path="t.jpg", width=800, height=200)])
    result = await view.list_threads("b", request_ns())
    assert result[0].op_post is not None
    assert result[0].op_post.width == 800
    assert result[0].op_post.height == 200


async def test_list_threads_maps_all_op_images():
    view, _ = build(
        op_images=[
            attachment_ns(thumbnail_path="t1.jpg", file_path="f1.png"),
            attachment_ns(thumbnail_path=None, file_path="f2.png"),
        ]
    )
    result = await view.list_threads("b", request_ns())
    images = result[0].op_post.images
    assert [image.thumbnail_url for image in images] == ["/media/t1.jpg", "/media/f2.png"]
    assert [image.url for image in images] == ["/media/f1.png", "/media/f2.png"]


async def test_list_threads_maps_last_replies():
    reply = post_ns(
        id=77,
        post_number=42,
        name="sdaf",
        body="reply body",
        body_html="<p>reply body</p>",
        created_at=datetime(2024, 6, 1),
    )
    view, _ = build(replies=[reply])
    result = await view.list_threads("b", request_ns())
    assert len(result[0].last_replies) == 1
    assert result[0].last_replies[0].id == 77
    assert result[0].last_replies[0].post_number == 42
    assert result[0].last_replies[0].name == "sdaf"
    assert result[0].last_replies[0].body == "reply body"
    assert result[0].last_replies[0].body_html == "<p>reply body</p>"


async def test_list_threads_touches_board_presence():
    view, mocks = build()
    await view.list_threads("b", request_ns())
    mocks.online_tracker.touch.assert_awaited_once()
    assert mocks.online_tracker.touch.await_args.args[1] == "b"


async def test_list_latest_threads_maps_responses():
    view, mocks = build()
    mocks.thread_service.list_latest_threads = AsyncMock(
        return_value=[
            (
                thread_ns(),
                "b",
                attachment_ns(thumbnail_path="t.jpg"),
                post_ns(id=15, post_number=88, body="latest", created_at=datetime(2026, 6, 10)),
            ),
            (thread_ns(id=6), "g", None, None),
        ]
    )

    result = await view.list_latest_threads(limit=5)

    mocks.thread_service.list_latest_threads.assert_awaited_once_with(5)
    assert result[0].board_slug == "b"
    assert result[0].thumbnail_url == "/media/t.jpg"
    assert result[0].last_reply is not None
    assert result[0].last_reply.post_number == 88
    assert result[0].last_reply.body == "latest"
    assert result[1].board_slug == "g"
    assert result[1].thumbnail_url is None
    assert result[1].last_reply is None


async def test_get_thread_statuses_maps_responses():
    view, mocks = build()
    mocks.thread_service.get_thread_statuses = AsyncMock(
        return_value=[(thread_ns(id=5, title="t", is_locked=True, reply_count=3), "b")]
    )

    result = await view.get_thread_statuses([5])

    mocks.thread_service.get_thread_statuses.assert_awaited_once_with([5])
    assert result[0].id == 5
    assert result[0].board_slug == "b"
    assert result[0].title == "t"
    assert result[0].is_locked is True
    assert result[0].reply_count == 3


async def test_get_thread_statuses_empty_list():
    view, mocks = build()
    mocks.thread_service.get_thread_statuses = AsyncMock(return_value=[])

    assert await view.get_thread_statuses([]) == []


async def test_get_thread_statuses_rejects_too_many_ids():
    view, mocks = build()
    mocks.thread_service.get_thread_statuses = AsyncMock(return_value=[])

    with pytest.raises(BadRequestError):
        await view.get_thread_statuses(list(range(51)))
    mocks.thread_service.get_thread_statuses.assert_not_called()


async def test_get_thread_includes_posts_with_attachments():
    view, _ = build()
    detail = await view.get_thread("b", 5, request_ns())
    assert isinstance(detail, ThreadDetailResponse)
    assert len(detail.posts) == 1
    assert len(detail.posts[0].attachments) == 1
    # the requester's ip differs from the post's ip_hash -> not editable
    assert detail.posts[0].can_edit is False


async def test_get_thread_marks_own_post_editable():
    from src.utils.ip import hash_ip

    view, mocks = build()
    viewer_ip_hash = hash_ip("1.2.3.4", "salt")
    mocks.thread_service.get_thread_detail = AsyncMock(
        return_value=(
            thread_ns(),
            [post_ns(id=10, ip_hash=viewer_ip_hash, created_at=utcnow())],
            {10: []},
        )
    )
    detail = await view.get_thread("b", 5, request_ns(host="1.2.3.4"))
    assert detail.posts[0].can_edit is True


async def test_create_thread_with_image_delegates(monkeypatch):
    monkeypatch.setattr(uploads_module, "process_attachment", SimpleNamespace(delay=MagicMock()))
    monkeypatch.setattr(uploads_module.celery, "send_task", MagicMock())
    view, mocks = build()

    result = await view.create_thread(
        "b", ThreadCreate(body="hi"), [upload_ns()], request_ns(), "tok", "ans"
    )

    assert isinstance(result, ThreadDetailResponse)
    assert len(result.posts) == 1
    # the op author may edit their own fresh post
    assert result.posts[0].can_edit is True
    mocks.captcha_service.validate.assert_awaited_once_with("tok", "ans")
    mocks.thread_service.create_thread.assert_awaited_once()
    # has_image computed from uploads and passed to the service
    assert mocks.thread_service.create_thread.await_args.kwargs["has_image"] is True
    mocks.file_service.store_attachment.assert_awaited_once()
    mocks.events.publish.assert_awaited_once()


async def test_create_thread_enqueues_embedding(embed_delay, monkeypatch):
    monkeypatch.setattr(uploads_module, "process_attachment", SimpleNamespace(delay=MagicMock()))
    monkeypatch.setattr(uploads_module.celery, "send_task", MagicMock())
    view, _ = build()
    await view.create_thread("b", ThreadCreate(body="hi"), [], request_ns(), "tok", "ans")
    embed_delay.assert_called_once_with(10)


async def test_create_thread_enqueues_text_moderation(moderate_send_task):
    view, _ = build()
    await view.create_thread("b", ThreadCreate(body="hi"), [], request_ns(), "tok", "ans")
    assert moderate_send_task.call_args.args[0] == "moderate_text"
    assert moderate_send_task.call_args.kwargs["args"] == [10, "hi"]
    assert moderate_send_task.call_args.kwargs["queue"] == "moderation"


async def test_create_thread_rate_limited():
    view, mocks = build(allowed=False)
    with pytest.raises(RateLimitedError):
        await view.create_thread("b", ThreadCreate(), [upload_ns()], request_ns(), "tok", "ans")
    mocks.thread_service.create_thread.assert_not_called()


async def test_create_thread_requires_captcha_when_missing():
    view, mocks = build()
    with pytest.raises(InvalidCaptchaError):
        await view.create_thread("b", ThreadCreate(body="hi"), [], request_ns(), None, None)
    mocks.captcha_service.validate.assert_not_called()
    mocks.thread_service.create_thread.assert_not_called()


async def test_create_thread_admin_skips_captcha(monkeypatch):
    monkeypatch.setattr(uploads_module, "process_attachment", SimpleNamespace(delay=MagicMock()))
    monkeypatch.setattr(uploads_module.celery, "send_task", MagicMock())
    view, mocks = build()
    mocks.mod_service.is_admin = AsyncMock(return_value=True)

    result = await view.create_thread(
        "b", ThreadCreate(body="hi"), [], request_ns(), None, None, admin_token="admin-jwt"
    )

    assert isinstance(result, ThreadDetailResponse)
    mocks.mod_service.is_admin.assert_awaited_once_with("admin-jwt")
    mocks.captcha_service.validate.assert_not_called()
    mocks.thread_service.create_thread.assert_awaited_once()
