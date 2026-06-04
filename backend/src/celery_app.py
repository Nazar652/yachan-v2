from celery import Celery
from celery.signals import worker_process_init

from src.core.config import get_settings

settings = get_settings()

# include so worker processes import (and thus register) the task modules;
# without it the worker only knows tasks reachable from src.celery_app and beat's
# "expire_bans" / enqueued "process_attachment" arrive unregistered.
celery = Celery(
    "yachan",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.tasks.attachments", "src.tasks.bans"],
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

    setup_di()
