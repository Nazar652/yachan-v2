import asyncio

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from src.bootstrap.scope import close_scope, current_scope, open_scope
from src.core.database import get_engine


class ScopedTask(Task):
    """Celery task that runs its async `run` inside a di scope, with the same
    commit/rollback/close lifecycle as the http scope middleware."""

    abstract = True

    def __call__(self, *args, **kwargs):
        return asyncio.run(self._run_scoped(*args, **kwargs))

    async def _run_scoped(self, *args, **kwargs):
        open_scope()
        try:
            result = await self.run(*args, **kwargs)
            await self._commit()
            return result
        except Exception:
            await self._rollback()
            raise
        finally:
            had_session = self._session() is not None
            await self._close()
            close_scope()
            # each task runs in its own asyncio.run() loop; asyncpg connections are
            # loop-bound, so drop the pool or the next task reuses a connection from
            # a dead loop ("got Future attached to a different loop")
            if had_session:
                await get_engine().dispose()

    @staticmethod
    def _session() -> AsyncSession | None:
        scope = current_scope()
        return scope.get(AsyncSession) if scope else None

    async def _commit(self) -> None:
        if session := self._session():
            await session.commit()

    async def _rollback(self) -> None:
        if session := self._session():
            await session.rollback()

    async def _close(self) -> None:
        if session := self._session():
            await session.close()
