from src.celery_app import celery
from src.services.ban_service import BanService
from src.tasks.base import ScopedTask


@celery.task(base=ScopedTask, name="expire_bans")
async def expire_bans() -> int:
    # periodic: deactivate bans whose expiry has passed; returns how many
    return await BanService().expire_due()
