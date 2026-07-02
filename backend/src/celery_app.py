from celery import Celery
from celery.signals import beat_init, worker_process_init

from src.core.config import get_settings

settings = get_settings()

celery = Celery(
    "yachan",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "src.tasks.attachments",
        "src.tasks.bans",
        "src.tasks.moderation",
    ],
)
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        "expire-bans": {"task": "expire_bans", "schedule": 300.0},
    },
)


@worker_process_init.connect
def _setup_worker_di(**_kwargs) -> None:
    from src.bootstrap.container import setup_di
    from src.core.sentry import init_sentry

    setup_di()
    init_sentry(get_settings())


@beat_init.connect
def _setup_beat_sentry(**_kwargs) -> None:
    from src.core.sentry import init_sentry

    init_sentry(get_settings())
