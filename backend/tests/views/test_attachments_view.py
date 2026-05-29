from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import src.views.attachments_view as attachments_view_module
from src.models.attachment import MediaType
from src.schemas.attachment import AttachmentResponse
from src.views.attachments_view import AttachmentsView
from tests.views._factories import post_ns


def _attachment_ns(**overrides):
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


async def test_add_attachment_stores_and_enqueues(monkeypatch):
    post_service = MagicMock()
    post_service.get_post = AsyncMock(return_value=post_ns(id=10))
    file_service = MagicMock()
    file_service.store_attachment = AsyncMock(return_value=_attachment_ns())
    storage = MagicMock()
    storage.public_url = MagicMock(side_effect=lambda key: f"/media/{key}")

    delay = MagicMock()
    monkeypatch.setattr(
        attachments_view_module, "process_attachment", SimpleNamespace(delay=delay)
    )

    view = AttachmentsView(
        file_service=file_service, post_service=post_service, storage=storage
    )
    result = await view.add_attachment("b", 1, "cat.png", b"bytes", "image/png")

    assert isinstance(result, AttachmentResponse)
    assert result.url == "/media/abc.png"
    assert result.thumbnail_url is None
    file_service.store_attachment.assert_awaited_once_with(10, "cat.png", b"bytes", "image/png")
    delay.assert_called_once_with(7)
