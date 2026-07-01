from unittest.mock import AsyncMock, MagicMock

from kink import di

from src.services.file_service import FileService
from src.tasks.attachments import process_attachment


def test_process_attachment_delegates_to_file_service(monkeypatch):
    instance = MagicMock()
    instance.process_attachment = AsyncMock()
    monkeypatch.setitem(di.factories, FileService, lambda container: instance)

    process_attachment(42)

    instance.process_attachment.assert_awaited_once_with(42)
