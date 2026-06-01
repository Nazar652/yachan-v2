from celery import Celery
from celery.signals import worker_process_init

from src.bootstrap.container import setup_di
from src.core.config import get_settings

settings = get_settings()

celery = Celery("yachan", broker=settings.redis_url, backend=settings.redis_url)
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
    # each worker process registers its own di container once on startup
    setup_di()
