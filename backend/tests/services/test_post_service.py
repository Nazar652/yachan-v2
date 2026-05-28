from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.clock import utcnow
from src.core.exceptions import (
    BoardNotFoundError,
    EditWindowExpiredError,
    IpBannedError,
    NotPostAuthorError,
    PostAlreadyEditedError,
    PostNotFoundError,
    ThreadLockedError,
    ThreadNotFoundError,
)
from src.schemas.post import PostCreate, PostEditCreate
from src.services.post_service import PostService

_UNSET = object()


def build(*, board=_UNSET, thread=_UNSET, refs=None):
    board_obj = SimpleNamespace(id=1, bump_limit=300) if board is _UNSET else board
    thread_obj = (
        SimpleNamespace(id=5, board_id=1, is_locked=False, reply_count=0)
        if thread is _UNSET
        else thread
    )
    created_post = SimpleNamespace(id=10, post_number=1)

    post_repo = MagicMock()
    post_repo.next_post_number = AsyncMock(return_value=1)
    post_repo.create = AsyncMock(return_value=created_post)
    post_repo.get_by_board_and_number = AsyncMock(return_value=None)

    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=board_obj)

    thread_repo = MagicMock()
    thread_repo.get_by_id = AsyncMock(return_value=thread_obj)
    thread_repo.increment_reply_count = AsyncMock()
    thread_repo.update_bump_at = AsyncMock()

    post_edit_repo = MagicMock()
    backlink_repo = MagicMock()
    backlink_repo.create_many = AsyncMock()

    markup = MagicMock()
    markup.render = MagicMock(return_value="<p>x</p>")
    markup.extract_refs = MagicMock(return_value=refs or [])

    ban_service = MagicMock()
    ban_service.assert_not_banned = AsyncMock()

    service = PostService(
        post_repo=post_repo,
        post_edit_repo=post_edit_repo,
        thread_repo=thread_repo,
        board_repo=board_repo,
        backlink_repo=backlink_repo,
        markup=markup,
        ban_service=ban_service,
    )
    mocks = SimpleNamespace(
        post_repo=post_repo,
        board_repo=board_repo,
        thread_repo=thread_repo,
        post_edit_repo=post_edit_repo,
        backlink_repo=backlink_repo,
        markup=markup,
        ban_service=ban_service,
        created_post=created_post,
    )
    return service, mocks


async def test_create_reply_happy_path_bumps_thread():
    service, mocks = build()

    result = await service.create_reply("b", 5, PostCreate(body="hi"), "iphash")

    assert result is mocks.created_post
    mocks.thread_repo.increment_reply_count.assert_awaited_once_with(5)
    mocks.thread_repo.update_bump_at.assert_awaited_once_with(5)


async def test_create_reply_sage_does_not_bump():
    service, mocks = build()

    await service.create_reply("b", 5, PostCreate(body="hi", sage=True), "iphash")

    mocks.thread_repo.increment_reply_count.assert_awaited_once()
    mocks.thread_repo.update_bump_at.assert_not_called()


async def test_create_reply_does_not_bump_past_limit():
    thread = SimpleNamespace(id=5, board_id=1, is_locked=False, reply_count=300)
    service, mocks = build(thread=thread)

    await service.create_reply("b", 5, PostCreate(body="hi"), "iphash")

    mocks.thread_repo.update_bump_at.assert_not_called()


async def test_create_reply_unknown_board():
    service, _ = build(board=None)
    with pytest.raises(BoardNotFoundError):
        await service.create_reply("b", 5, PostCreate(), "iphash")


async def test_create_reply_unknown_thread():
    service, mocks = build()
    mocks.thread_repo.get_by_id = AsyncMock(return_value=None)
    with pytest.raises(ThreadNotFoundError):
        await service.create_reply("b", 5, PostCreate(), "iphash")


async def test_create_reply_thread_from_other_board():
    thread = SimpleNamespace(id=5, board_id=999, is_locked=False, reply_count=0)
    service, _ = build(thread=thread)
    with pytest.raises(ThreadNotFoundError):
        await service.create_reply("b", 5, PostCreate(), "iphash")


async def test_create_reply_locked_thread():
    thread = SimpleNamespace(id=5, board_id=1, is_locked=True, reply_count=0)
    service, _ = build(thread=thread)
    with pytest.raises(ThreadLockedError):
        await service.create_reply("b", 5, PostCreate(), "iphash")


async def test_create_reply_banned():
    service, mocks = build()
    mocks.ban_service.assert_not_banned = AsyncMock(side_effect=IpBannedError())
    with pytest.raises(IpBannedError):
        await service.create_reply("b", 5, PostCreate(), "iphash")


async def test_create_reply_stores_backlinks():
    service, mocks = build(refs=[7])
    mocks.post_repo.get_by_board_and_number = AsyncMock(return_value=SimpleNamespace(id=20))

    await service.create_reply("b", 5, PostCreate(body="see >>7"), "iphash")

    mocks.backlink_repo.create_many.assert_awaited_once()


async def test_create_reply_no_backlinks_when_no_refs():
    service, mocks = build(refs=[])
    await service.create_reply("b", 5, PostCreate(body="hi"), "iphash")
    mocks.backlink_repo.create_many.assert_not_called()


def _edit_service(post):
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=SimpleNamespace(id=1))
    post_repo = MagicMock()
    post_repo.get_by_board_and_number = AsyncMock(return_value=post)
    post_repo.mark_edited = AsyncMock(return_value=SimpleNamespace(id=getattr(post, "id", 1)))
    post_edit_repo = MagicMock()
    post_edit_repo.create = AsyncMock()
    markup = MagicMock()
    markup.render = MagicMock(return_value="<p>new</p>")
    service = PostService(
        post_repo=post_repo,
        post_edit_repo=post_edit_repo,
        thread_repo=MagicMock(),
        board_repo=board_repo,
        backlink_repo=MagicMock(),
        markup=markup,
        ban_service=MagicMock(),
    )
    return service, SimpleNamespace(post_repo=post_repo, post_edit_repo=post_edit_repo)


async def test_edit_post_happy_path_saves_original():
    post = SimpleNamespace(
        id=10, ip_hash="me", is_edited=False, created_at=utcnow(), body="old", body_html="<p>old</p>"
    )
    service, mocks = _edit_service(post)

    await service.edit_post("b", 1, PostEditCreate(new_body="new"), "me")

    mocks.post_edit_repo.create.assert_awaited_once()
    mocks.post_repo.mark_edited.assert_awaited_once()


async def test_edit_post_wrong_author():
    post = SimpleNamespace(id=10, ip_hash="someone", is_edited=False, created_at=utcnow())
    service, _ = _edit_service(post)
    with pytest.raises(NotPostAuthorError):
        await service.edit_post("b", 1, PostEditCreate(new_body="x"), "me")


async def test_edit_post_already_edited():
    post = SimpleNamespace(id=10, ip_hash="me", is_edited=True, created_at=utcnow())
    service, _ = _edit_service(post)
    with pytest.raises(PostAlreadyEditedError):
        await service.edit_post("b", 1, PostEditCreate(new_body="x"), "me")


async def test_edit_post_window_expired():
    post = SimpleNamespace(
        id=10, ip_hash="me", is_edited=False, created_at=utcnow() - timedelta(hours=1)
    )
    service, _ = _edit_service(post)
    with pytest.raises(EditWindowExpiredError):
        await service.edit_post("b", 1, PostEditCreate(new_body="x"), "me")


async def test_edit_post_missing_post():
    service, mocks = _edit_service(None)
    with pytest.raises(PostNotFoundError):
        await service.edit_post("b", 1, PostEditCreate(new_body="x"), "me")


async def test_get_post_history_returns_edit():
    post = SimpleNamespace(id=10)
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=SimpleNamespace(id=1))
    post_repo = MagicMock()
    post_repo.get_by_board_and_number = AsyncMock(return_value=post)
    post_edit_repo = MagicMock()
    edit = object()
    post_edit_repo.get_by_post_id = AsyncMock(return_value=edit)
    service = PostService(
        post_repo=post_repo,
        post_edit_repo=post_edit_repo,
        thread_repo=MagicMock(),
        board_repo=board_repo,
        backlink_repo=MagicMock(),
        markup=MagicMock(),
        ban_service=MagicMock(),
    )

    assert await service.get_post_history("b", 1) is edit
