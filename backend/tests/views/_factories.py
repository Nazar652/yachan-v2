from datetime import datetime
from types import SimpleNamespace

_NOW = datetime(2026, 1, 1)


def board_ns(**overrides):
    data = dict(
        id=1,
        slug="b",
        title="Random",
        description=None,
        bump_limit=300,
        is_active=True,
        created_at=_NOW,
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def thread_ns(**overrides):
    data = dict(
        id=5,
        board_id=1,
        title="hello",
        is_locked=False,
        is_sticky=False,
        reply_count=0,
        bump_at=_NOW,
        created_at=_NOW,
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def post_ns(**overrides):
    data = dict(
        id=10,
        post_number=1,
        thread_id=5,
        board_id=1,
        name="Anonymous",
        tripcode=None,
        body="hi",
        body_html="<p>hi</p>",
        sage=False,
        is_op=False,
        is_edited=False,
        edited_at=None,
        created_at=_NOW,
        ip_hash="secret",
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def report_ns(**overrides):
    data = dict(
        id=1,
        post_id=10,
        board_id=1,
        reason="spam",
        is_resolved=False,
        created_at=_NOW,
        ip_hash="secret",
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def ban_ns(**overrides):
    data = dict(
        id=1,
        ip_hash="poster",
        board_id=1,
        reason="spam",
        expires_at=None,
        is_active=True,
        created_at=_NOW,
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def attachment_ns(**overrides):
    from src.models.attachment import MediaType

    data = dict(
        id=7,
        media_type=MediaType.IMAGE,
        original_name="cat.png",
        file_path="abc.png",
        thumbnail_path=None,
        mime_type="image/png",
        width=None,
        height=None,
        duration_seconds=None,
        size_bytes=100,
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def upload_ns(filename="cat.png", content=b"bytes", content_type="image/png"):
    from unittest.mock import AsyncMock, MagicMock

    upload = MagicMock()
    upload.filename = filename
    upload.content_type = content_type
    upload.read = AsyncMock(return_value=content)
    return upload


def request_ns(host="1.2.3.4"):
    return SimpleNamespace(client=SimpleNamespace(host=host))


def settings_ns():
    return SimpleNamespace(ip_hash_salt="salt")
