import logging

from celery import Celery
from celery.signals import before_task_publish, beat_init, worker_process_init

from src.core.config import get_settings
from src.core.logging import log_event
from src.utils.request_context import get_request_id

settings = get_settings()
logger = logging.getLogger("src.tasks")

celery = Celery(
    "yachan",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "src.tasks.attachments",
        "src.tasks.bans",
        "src.tasks.moderation",
        "src.tasks.search",
        "src.tasks.summary",
    ],
)
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        "expire-bans": {"task": "expire_bans", "schedule": 300.0},
        "summarize-stale-threads": {"task": "summarize_stale_threads", "schedule": 300.0},
    },
)


@worker_process_init.connect
def _setup_worker_di(**_kwargs) -> None:
    from src.bootstrap.container import setup_di
    from src.core.logging import configure_logging
    from src.core.sentry import init_sentry

    setup_di()
    configure_logging(settings.debug)
    init_sentry(get_settings())


@beat_init.connect
def _setup_beat_sentry(**_kwargs) -> None:
    from src.core.logging import configure_logging
    from src.core.sentry import init_sentry

    configure_logging(settings.debug)
    init_sentry(get_settings())


@before_task_publish.connect
def _log_task_enqueued(sender=None, headers=None, routing_key=None, **_kwargs) -> None:
    # stamps the producer's request_id onto the message so the worker (a
    # different process) can pick up the same correlation id in ScopedTask
    if headers is not None:
        headers["request_id"] = get_request_id()

    log_event(
        logger,
        "task_enqueued",
        task_name=sender,
        task_id=(headers or {}).get("id"),
        queue=routing_key,
    )
