from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from src.core.config import get_settings
from src.core.database import get_engine, get_sessionmaker, new_session


def test_get_engine_is_cached_and_async():
    engine = get_engine()
    assert isinstance(engine, AsyncEngine)
    assert engine.url.drivername == "postgresql+asyncpg"
    assert get_engine() is engine


def test_get_engine_recycles_stale_connections():
    pool = get_engine().pool
    assert pool._pre_ping is True
    assert pool._recycle == get_settings().db_pool_recycle


def test_get_sessionmaker_is_cached():
    assert get_sessionmaker() is get_sessionmaker()


async def test_new_session_returns_async_session():
    session = new_session()
    assert isinstance(session, AsyncSession)
    await session.close()
