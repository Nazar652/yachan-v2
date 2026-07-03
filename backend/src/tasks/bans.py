from kink import inject

from src.celery_app import celery
from src.services.ban_service import BanService
from src.tasks.base import ScopedTask


@celery.task(base=ScopedTask, name="expire_bans", typing=False)
@inject
async def expire_bans(ban_service: BanService) -> int:
    # periodic: deactivate bans whose expiry has passed; returns how many
    return await ban_service.expire_due()
