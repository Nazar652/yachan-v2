from kink import inject

from src.celery_app import celery
from src.services.file_service import FileService
from src.tasks.base import ScopedTask


@celery.task(base=ScopedTask, name="process_attachment", typing=False)
@inject
async def process_attachment(attachment_id: int, file_service: FileService) -> None:
    await file_service.process_attachment(attachment_id)
