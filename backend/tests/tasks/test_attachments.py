from unittest.mock import AsyncMock, MagicMock

import src.tasks.attachments as attachments_task
from src.tasks.attachments import process_attachment


def test_process_attachment_delegates_to_file_service(monkeypatch):
    instance = MagicMock()
    instance.process_attachment = AsyncMock()
    factory = MagicMock(return_value=instance)
    monkeypatch.setattr(attachments_task, "FileService", factory)

    process_attachment(42)

    instance.process_attachment.assert_awaited_once_with(42)
