from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import src.views.uploads as uploads_module
from src.core.exceptions import TooManyAttachmentsError, UnsupportedMediaTypeError
from src.models.attachment import MediaType
from src.views.uploads import Upload, contains_image, read_uploads, store_uploads
from tests.views._factories import attachment_ns, upload_ns


async def test_read_uploads_reads_and_classifies():
    uploads = await read_uploads([upload_ns(filename="cat.png", content_type="image/png")])
    assert len(uploads) == 1
    assert uploads[0].media_type is MediaType.IMAGE


async def test_read_uploads_skips_empty_entries():
    empty = upload_ns(filename="", content=b"")
    uploads = await read_uploads([empty])
    assert uploads == []


async def test_read_uploads_rejects_unsupported_type():
    with pytest.raises(UnsupportedMediaTypeError):
        await read_uploads([upload_ns(content_type="text/plain")])


async def test_read_uploads_enforces_limit():
    files = [upload_ns(filename=f"{i}.png") for i in range(11)]
    with pytest.raises(TooManyAttachmentsError):
        await read_uploads(files)


def test_contains_image_true_for_image():
    uploads = [Upload("c.png", b"x", "image/png", MediaType.IMAGE)]
    assert contains_image(uploads) is True


def test_contains_image_false_for_video_only():
    uploads = [Upload("v.mp4", b"x", "video/mp4", MediaType.VIDEO)]
    assert contains_image(uploads) is False


async def test_store_uploads_stores_and_enqueues(monkeypatch):
    delay = MagicMock()
    monkeypatch.setattr(uploads_module, "process_attachment", SimpleNamespace(delay=delay))
    send_task = MagicMock()
    monkeypatch.setattr(uploads_module.celery, "send_task", send_task)
    file_service = MagicMock()
    file_service.store_attachment = AsyncMock(return_value=attachment_ns(id=7, file_path="abc.png"))
    file_service.storage.public_url = MagicMock(return_value="http://media/abc.png")

    uploads = [Upload("c.png", b"x", "image/png", MediaType.IMAGE)]
    stored = await store_uploads(file_service, post_id=10, uploads=uploads)

    assert len(stored) == 1
    file_service.store_attachment.assert_awaited_once_with(10, "c.png", b"x", "image/png")
    delay.assert_called_once_with(7)
    file_service.storage.public_url.assert_called_once_with("abc.png")
    send_task.assert_called_once()
    assert send_task.call_args.args[0] == "moderate_image"
    assert send_task.call_args.kwargs["queue"] == "moderation"
    assert send_task.call_args.kwargs["args"] == [7, "http://media/abc.png", "nsfw"]
