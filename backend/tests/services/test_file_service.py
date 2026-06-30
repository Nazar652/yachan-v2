import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from PIL import Image
from src.core.exceptions import FileTooLargeError, UnsupportedMediaTypeError
from src.models.attachment import MediaType
from src.services.file_service import MAX_UPLOAD_BYTES, FileService


def _png_bytes(size=(20, 10)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="PNG")
    return buffer.getvalue()


def _jpeg_with_orientation(size, orientation) -> bytes:
    image = Image.new("RGB", size, "red")
    exif = image.getexif()
    exif[0x0112] = orientation
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


def test_media_type_for_maps_known_types():
    assert FileService.media_type_for("image/png") is MediaType.IMAGE
    assert FileService.media_type_for("image/gif") is MediaType.GIF
    assert FileService.media_type_for("video/mp4") is MediaType.VIDEO


def test_media_type_for_rejects_unknown():
    with pytest.raises(UnsupportedMediaTypeError):
        FileService.media_type_for("text/plain")


async def test_store_attachment_saves_new_file():
    attachment_repo = MagicMock()
    attachment_repo.get_by_md5 = AsyncMock(return_value=None)
    attachment_repo.create = AsyncMock(return_value=SimpleNamespace(id=1))
    storage = MagicMock()
    storage.save = AsyncMock()
    service = FileService(attachment_repo=attachment_repo, storage=storage)

    await service.store_attachment(5, "cat.png", b"bytes", "image/png")

    storage.save.assert_awaited_once()
    attachment_repo.create.assert_awaited_once()


async def test_store_attachment_dedups_existing_md5():
    attachment_repo = MagicMock()
    attachment_repo.get_by_md5 = AsyncMock(
        return_value=SimpleNamespace(file_path="existing.png")
    )
    attachment_repo.create = AsyncMock(return_value=SimpleNamespace(id=2))
    storage = MagicMock()
    storage.save = AsyncMock()
    service = FileService(attachment_repo=attachment_repo, storage=storage)

    await service.store_attachment(5, "dup.png", b"bytes", "image/png")

    storage.save.assert_not_awaited()
    attachment_repo.create.assert_awaited_once()


async def test_store_attachment_rejects_unsupported_type():
    service = FileService(attachment_repo=MagicMock(), storage=MagicMock())
    with pytest.raises(UnsupportedMediaTypeError):
        await service.store_attachment(5, "x.txt", b"data", "text/plain")


async def test_store_attachment_rejects_too_large():
    attachment_repo = MagicMock()
    attachment_repo.get_by_md5 = AsyncMock(return_value=None)
    service = FileService(attachment_repo=attachment_repo, storage=MagicMock())
    with pytest.raises(FileTooLargeError):
        await service.store_attachment(
            5, "big.png", b"x" * (MAX_UPLOAD_BYTES + 1), "image/png"
        )


async def test_process_attachment_image_sets_dimensions_and_thumbnail():
    attachment = SimpleNamespace(media_type=MediaType.IMAGE, file_path="k.png", md5="abc")
    attachment_repo = MagicMock()
    attachment_repo.get_by_id = AsyncMock(return_value=attachment)
    attachment_repo.set_media_info = AsyncMock()
    storage = MagicMock()
    storage.read = AsyncMock(return_value=_png_bytes((20, 10)))
    storage.save = AsyncMock()
    service = FileService(attachment_repo=attachment_repo, storage=storage)

    await service.process_attachment(1)

    storage.save.assert_awaited_once()
    attachment_repo.set_media_info.assert_awaited_once()
    kwargs = attachment_repo.set_media_info.await_args.kwargs
    assert kwargs["width"] == 20
    assert kwargs["height"] == 10


async def test_process_attachment_applies_exif_orientation():
    attachment = SimpleNamespace(media_type=MediaType.IMAGE, file_path="k.jpg", md5="abc")
    attachment_repo = MagicMock()
    attachment_repo.get_by_id = AsyncMock(return_value=attachment)
    attachment_repo.set_media_info = AsyncMock()
    storage = MagicMock()
    # stored sideways (20x10) with orientation 6 (rotate 90) -> displays as 10x20
    storage.read = AsyncMock(return_value=_jpeg_with_orientation((20, 10), 6))
    storage.save = AsyncMock()
    service = FileService(attachment_repo=attachment_repo, storage=storage)

    await service.process_attachment(1)

    kwargs = attachment_repo.set_media_info.await_args.kwargs
    assert kwargs["width"] == 10
    assert kwargs["height"] == 20


async def test_process_attachment_skips_video():
    attachment = SimpleNamespace(media_type=MediaType.VIDEO, file_path="k.mp4", md5="abc")
    attachment_repo = MagicMock()
    attachment_repo.get_by_id = AsyncMock(return_value=attachment)
    attachment_repo.set_media_info = AsyncMock()
    service = FileService(attachment_repo=attachment_repo, storage=MagicMock())

    await service.process_attachment(1)

    attachment_repo.set_media_info.assert_not_called()


async def test_process_attachment_missing_is_noop():
    attachment_repo = MagicMock()
    attachment_repo.get_by_id = AsyncMock(return_value=None)
    attachment_repo.set_media_info = AsyncMock()
    service = FileService(attachment_repo=attachment_repo, storage=MagicMock())

    await service.process_attachment(999)

    attachment_repo.set_media_info.assert_not_called()
