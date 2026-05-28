from kink import di
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.core.database import AsyncSessionLocal

from .scope import resolve_scoped


def setup_di() -> None:
    settings = Settings()  # type: ignore[call-arg]
    di[Settings] = settings

    # one AsyncSession per request, shared by every repository in that request
    # so they all run inside the same transaction
    di[AsyncSession] = lambda di: resolve_scoped(AsyncSession, factory=AsyncSessionLocal)
