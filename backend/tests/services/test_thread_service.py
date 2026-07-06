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
    attachment_repo.list_images_by_post_ids = AsyncMock(return_value={})
    attachment_repo.get_first_images_by_post_ids = AsyncMock(return_value={})
    attachment_repo.list_by_thread = AsyncMock(return_value=[])
    attachment_repo.delete_by_post_ids = AsyncMock()
    attachment_repo.count_by_file_path = AsyncMock(return_value=0)
    post_repo.list_ids_by_thread = AsyncMock(return_value=[op_post.id])
    post_repo.delete_by_thread = AsyncMock()
    thread_repo.delete = AsyncMock()
    thread_repo.flush = AsyncMock()
    backlink_repo = MagicMock()
    backlink_repo.delete_by_post_ids = AsyncMock()
    post_edit_repo = MagicMock()
    post_edit_repo.delete_by_post_ids = AsyncMock()
    report_repo = MagicMock()
    report_repo.delete_by_post_ids = AsyncMock()
    storage = MagicMock()
    storage.delete = AsyncMock()
    markup = MagicMock()
    markup.render = MagicMock(return_value="<p>x</p>")
    ban_service = MagicMock()
    ban_service.assert_not_banned = AsyncMock()

    service = ThreadService(
        thread_repo=thread_repo,
        post_repo=post_repo,
        board_repo=board_repo,
        attachment_repo=attachment_repo,
        backlink_repo=backlink_repo,
        post_edit_repo=post_edit_repo,
        report_repo=report_repo,
        storage=storage,
        markup=markup,
        ban_service=ban_service,
    )
    return service, SimpleNamespace(
        board_repo=board_repo,
        thread_repo=thread_repo,
        post_repo=post_repo,
        attachment_repo=attachment_repo,
        backlink_repo=backlink_repo,
        post_edit_repo=post_edit_repo,
        report_repo=report_repo,
        storage=storage,
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


async def test_delete_thread_removes_rows_and_returns_thread():
    service, mocks = build()

    result = await service.delete_thread("b", 5)

    assert result is mocks.thread
    mocks.backlink_repo.delete_by_post_ids.assert_awaited_once_with([mocks.op_post.id])
    mocks.post_edit_repo.delete_by_post_ids.assert_awaited_once_with([mocks.op_post.id])
    mocks.report_repo.delete_by_post_ids.assert_awaited_once_with([mocks.op_post.id])
    mocks.attachment_repo.delete_by_post_ids.assert_awaited_once_with([mocks.op_post.id])
    mocks.post_repo.delete_by_thread.assert_awaited_once_with(5)
    mocks.thread_repo.delete.assert_awaited_once_with(5)


async def test_delete_thread_unknown_board():
    service, _ = build(board=None)
    with pytest.raises(BoardNotFoundError):
        await service.delete_thread("b", 5)


async def test_delete_thread_wrong_board():
    service, mocks = build()
    mocks.thread_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(id=5, board_id=999))
    with pytest.raises(ThreadNotFoundError):
        await service.delete_thread("b", 5)


async def test_delete_thread_deletes_only_orphaned_blobs():
    service, mocks = build()
    shared = SimpleNamespace(file_path="shared.jpg", thumbnail_path="thumb/shared.jpg")
    orphan = SimpleNamespace(file_path="orphan.png", thumbnail_path=None)
    mocks.attachment_repo.list_by_thread = AsyncMock(return_value=[shared, orphan])
    # shared.jpg still referenced elsewhere, orphan.png is not
    mocks.attachment_repo.count_by_file_path = AsyncMock(side_effect=[1, 0])

    await service.delete_thread("b", 5)

    mocks.storage.delete.assert_awaited_once_with("orphan.png")


async def test_delete_thread_deletes_blob_and_thumbnail():
    service, mocks = build()
    att = SimpleNamespace(file_path="a.jpg", thumbnail_path="thumb/a.jpg")
    mocks.attachment_repo.list_by_thread = AsyncMock(return_value=[att])
    mocks.attachment_repo.count_by_file_path = AsyncMock(return_value=0)

    await service.delete_thread("b", 5)

    assert mocks.storage.delete.await_count == 2


async def test_list_threads_returns_tuples_with_preview():
    service, mocks = build()
    mocks.thread_repo.list_by_board = AsyncMock(return_value=[mocks.thread])

    result = await service.list_threads("b")

    assert len(result) == 1
    thread, op_post, op_images, replies = result[0]
    assert thread is mocks.thread
    assert op_post is mocks.op_post
    # no image attachment in default mock
    assert op_images == []
    assert replies == []
    mocks.post_repo.get_op_posts_by_thread_ids.assert_awaited_once_with([mocks.thread.id])
    mocks.attachment_repo.list_images_by_post_ids.assert_awaited_once()
    mocks.post_repo.get_last_replies_by_thread_ids.assert_awaited_once_with([mocks.thread.id])


async def test_list_threads_unknown_board():
    service, _ = build(board=None)
    with pytest.raises(BoardNotFoundError):
        await service.list_threads("b")


async def test_list_latest_threads_resolves_slug_image_and_last_reply():
    service, mocks = build()
    mocks.thread_repo.list_latest = AsyncMock(return_value=[mocks.thread])
    mocks.board_repo.list_all = AsyncMock(return_value=[SimpleNamespace(id=1, slug="b")])
    first_image = SimpleNamespace(id=3)
    mocks.attachment_repo.get_first_images_by_post_ids = AsyncMock(
        return_value={mocks.op_post.id: first_image}
    )
    last_reply = SimpleNamespace(id=15)
    mocks.post_repo.get_last_replies_by_thread_ids = AsyncMock(
        return_value={mocks.thread.id: [last_reply]}
    )

    result = await service.list_latest_threads(limit=5)

    assert result == [(mocks.thread, "b", first_image, last_reply)]
    mocks.thread_repo.list_latest.assert_awaited_once_with(5)
    mocks.post_repo.get_last_replies_by_thread_ids.assert_awaited_once_with(
        [mocks.thread.id], limit_per_thread=1
    )


async def test_list_latest_threads_without_replies_or_images():
    service, mocks = build()
    mocks.thread_repo.list_latest = AsyncMock(return_value=[mocks.thread])
    mocks.board_repo.list_all = AsyncMock(return_value=[SimpleNamespace(id=1, slug="b")])

    result = await service.list_latest_threads()

    assert result == [(mocks.thread, "b", None, None)]


async def test_get_thread_statuses_resolves_board_slug():
    service, mocks = build()
    mocks.thread_repo.list_by_ids = AsyncMock(return_value=[mocks.thread])
    mocks.board_repo.list_all = AsyncMock(return_value=[SimpleNamespace(id=1, slug="b")])

    result = await service.get_thread_statuses([mocks.thread.id])

    assert result == [(mocks.thread, "b")]
    mocks.thread_repo.list_by_ids.assert_awaited_once_with([mocks.thread.id])


async def test_get_thread_statuses_empty_input_skips_board_lookup():
    service, mocks = build()
    mocks.thread_repo.list_by_ids = AsyncMock(return_value=[])

    result = await service.get_thread_statuses([])

    assert result == []
    mocks.board_repo.list_all.assert_not_called()
