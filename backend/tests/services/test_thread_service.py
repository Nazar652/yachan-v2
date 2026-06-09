from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.exceptions import (
    BoardNotFoundError,
    IpBannedError,
    OpRequiresImageError,
    ThreadNotFoundError,
)
from src.schemas.thread import ThreadCreate
from src.services.thread_service import ThreadService

_UNSET = object()


def build(*, board=_UNSET):
    board_obj = SimpleNamespace(id=1) if board is _UNSET else board
    thread_obj = SimpleNamespace(id=5, board_id=1)
    op_post = SimpleNamespace(id=10, post_number=1)

    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=board_obj)
    thread_repo = MagicMock()
    thread_repo.create = AsyncMock(return_value=thread_obj)
    thread_repo.get_by_id = AsyncMock(return_value=thread_obj)
    post_repo = MagicMock()
    post_repo.next_post_number = AsyncMock(return_value=1)
    post_repo.create = AsyncMock(return_value=op_post)
    post_repo.get_thread_posts = AsyncMock(return_value=[op_post])
    post_repo.get_op_posts_by_thread_ids = AsyncMock(return_value={thread_obj.id: op_post})
    post_repo.get_last_replies_by_thread_ids = AsyncMock(return_value={})
    attachment_repo = MagicMock()
    attachment_repo.list_by_post_ids = AsyncMock(return_value={})
    attachment_repo.get_first_images_by_post_ids = AsyncMock(return_value={})
    markup = MagicMock()
    markup.render = MagicMock(return_value="<p>x</p>")
    ban_service = MagicMock()
    ban_service.assert_not_banned = AsyncMock()

    service = ThreadService(
        thread_repo=thread_repo,
        post_repo=post_repo,
        board_repo=board_repo,
        attachment_repo=attachment_repo,
        markup=markup,
        ban_service=ban_service,
    )
    return service, SimpleNamespace(
        board_repo=board_repo,
        thread_repo=thread_repo,
        post_repo=post_repo,
        attachment_repo=attachment_repo,
        ban_service=ban_service,
        thread=thread_obj,
        op_post=op_post,
    )


async def test_create_thread_creates_thread_and_op():
    service, mocks = build()

    thread, op_post = await service.create_thread(
        "b", ThreadCreate(body="hi"), "iphash", has_image=True
    )

    assert thread is mocks.thread
    assert op_post is mocks.op_post
    mocks.thread_repo.create.assert_awaited_once()
    mocks.post_repo.create.assert_awaited_once()


async def test_create_thread_without_image_rejected():
    service, mocks = build()
    with pytest.raises(OpRequiresImageError):
        await service.create_thread("b", ThreadCreate(body="hi"), "iphash", has_image=False)
    mocks.thread_repo.create.assert_not_called()


async def test_create_thread_unknown_board():
    service, _ = build(board=None)
    with pytest.raises(BoardNotFoundError):
        await service.create_thread("b", ThreadCreate(), "iphash", has_image=True)


async def test_create_thread_banned():
    service, mocks = build()
    mocks.ban_service.assert_not_banned = AsyncMock(side_effect=IpBannedError())
    with pytest.raises(IpBannedError):
        await service.create_thread("b", ThreadCreate(), "iphash", has_image=True)


async def test_get_thread_detail_returns_thread_posts_and_attachments():
    service, mocks = build()
    thread, posts, attachments_by_post = await service.get_thread_detail("b", 5)
    assert thread is mocks.thread
    assert posts == [mocks.op_post]
    assert attachments_by_post == {}
    mocks.attachment_repo.list_by_post_ids.assert_awaited_once_with([mocks.op_post.id])


async def test_get_thread_detail_wrong_board():
    service, mocks = build()
    mocks.thread_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(id=5, board_id=999))
    with pytest.raises(ThreadNotFoundError):
        await service.get_thread_detail("b", 5)


async def test_list_threads_returns_tuples_with_preview():
    service, mocks = build()
    mocks.thread_repo.list_by_board = AsyncMock(return_value=[mocks.thread])

    result = await service.list_threads("b")

    assert len(result) == 1
    thread, op_post, first_image, replies = result[0]
    assert thread is mocks.thread
    assert op_post is mocks.op_post
    # no image attachment in default mock
    assert first_image is None
    assert replies == []
    mocks.post_repo.get_op_posts_by_thread_ids.assert_awaited_once_with([mocks.thread.id])
    mocks.attachment_repo.get_first_images_by_post_ids.assert_awaited_once()
    mocks.post_repo.get_last_replies_by_thread_ids.assert_awaited_once_with([mocks.thread.id])


async def test_list_threads_unknown_board():
    service, _ = build(board=None)
    with pytest.raises(BoardNotFoundError):
        await service.list_threads("b")
