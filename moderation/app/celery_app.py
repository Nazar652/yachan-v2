from celery import Celery

from app.config import settings

# no result backend: the verdict returns as its own one-way task on `moderation_results`
celery = Celery("moderation", broker=settings.redis_url, include=["app.tasks"])
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)
