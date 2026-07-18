from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()

    # every connection is fresh with NullPool, so pre-ping/recycle would be noise
    if settings.db_use_null_pool:
        return create_async_engine(
            settings.database_url,
            echo=settings.db_echo,
            poolclass=NullPool,
        )

    return create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
        pool_recycle=settings.db_pool_recycle,
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False keeps attributes readable after the scope middleware
    # commits, since the view has already serialized the response by then
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


def new_session() -> AsyncSession:
    return get_sessionmaker()()
