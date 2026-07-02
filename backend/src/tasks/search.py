from kink import inject

from src.celery_app import celery
from src.services.search_service import SearchService
from src.tasks.base import ScopedTask


# typing=False: the injected service is part of the signature, so celery's producer-side
# arg check must be off for delay to pass just the message args
@celery.task(base=ScopedTask, name="embed_post", typing=False)
@inject
async def embed_post(post_id: int, search_service: SearchService) -> None:
    await search_service.index_post(post_id)
