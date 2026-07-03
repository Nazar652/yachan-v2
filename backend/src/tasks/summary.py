from kink import inject

from src.celery_app import celery
from src.core.config import get_settings
from src.services.summary_service import SummaryService
from src.tasks.base import ScopedTask


@celery.task(base=ScopedTask, name="summarize_thread", typing=False)
@inject
async def summarize_thread(thread_id: int, summary_service: SummaryService) -> None:
    await summary_service.summarize_thread(thread_id)


@celery.task(base=ScopedTask, name="summarize_stale_threads", typing=False)
@inject
async def summarize_stale_threads(summary_service: SummaryService) -> None:
    # periodic: enqueue a summary for every thread that grew enough since its last.
    # no api key means the feature is off, so do nothing rather than enqueue work.
    if not get_settings().gemini_api_key:
        return
    for thread_id in await summary_service.stale_thread_ids():
        summarize_thread.delay(thread_id)  # type: ignore[attr-defined]  celery task
