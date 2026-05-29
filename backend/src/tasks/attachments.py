from src.celery_app import celery
from src.services.file_service import FileService
from src.tasks.base import ScopedTask


@celery.task(base=ScopedTask, name="process_attachment")
async def process_attachment(attachment_id: int) -> None:
    # FileService() triggers kink injection: scoped repos + session
    await FileService().process_attachment(attachment_id)
