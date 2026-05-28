from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import Settings

settings = Settings()

engine = create_async_engine(settings.database_url, echo=settings.db_echo)

# expire_on_commit=False keeps attributes readable after the scope middleware
# commits, since the view has already serialized the response by then
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
