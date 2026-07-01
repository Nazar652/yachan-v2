from src.bootstrap.container import get_dependency
from src.celery_app import celery
from src.services.moderation_service import ModerationService
from src.tasks.base import ScopedTask


@celery.task(base=ScopedTask, name="apply_moderation_verdict")
async def apply_moderation_verdict(attachment_id: int, verdict: dict[str, object]) -> None:
    # resolve the service from the container, same as routers resolve views
    await get_dependency(ModerationService).apply(attachment_id, verdict)
