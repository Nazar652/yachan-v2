from kink import inject

from src.celery_app import celery
from src.services.moderation_service import ModerationService
from src.services.report_service import ReportService
from src.tasks.base import ScopedTask


# typing=False: the injected service is part of the signature, so celery's producer-side
# arg check must be off for send_task/delay to pass just the message args
@celery.task(base=ScopedTask, name="apply_moderation_verdict", typing=False)
@inject
async def apply_moderation_verdict(
    attachment_id: int, verdict: dict[str, object], moderation_service: ModerationService
) -> None:
    await moderation_service.apply(attachment_id, verdict)


@celery.task(base=ScopedTask, name="apply_text_verdict", typing=False)
@inject
async def apply_text_verdict(
    post_id: int, verdict: dict[str, object], report_service: ReportService
) -> None:
    # toxic/spam text is auto-reported (not hidden) for a human mod to decide
    await report_service.apply_text_verdict(post_id, verdict)
