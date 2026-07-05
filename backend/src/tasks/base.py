import asyncio
import logging
from time import perf_counter

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from src.bootstrap.scope import close_scope, current_scope, open_scope
from src.core.database import get_engine
from src.core.logging import log_event
from src.utils.request_context import set_request_id

logger = logging.getLogger("src.tasks")


class ScopedTask(Task):
    """Celery task that runs its async `run` inside a di scope, with the same
    commit/rollback/close lifecycle as the http scope middleware."""

    abstract = True

    def __call__(self, *args, **kwargs):
        return asyncio.run(self._run_scoped(*args, **kwargs))

    async def _run_scoped(self, *args, **kwargs):
        # the request_id producer-side stamped onto the message headers (see
        # celery_app._log_task_enqueued) so this task's own logs, and anything
        # it calls, correlate back to the request that enqueued it
        set_request_id((self.request.headers or {}).get("request_id"))
        start = perf_counter()
        status = "success"
        error = None

        open_scope()
        try:
            result = await self.run(*args, **kwargs)
            await self._commit()
            return result
        except Exception as exc:
            status = "failure"
            error = str(exc)
            await self._rollback()
            raise
        finally:
            had_session = self._session() is not None
            await self._close()
            close_scope()

            log_event(
                logger,
                "task_invoked",
                task_name=self.name,
                task_id=self.request.id,
                status=status,
                error=error,
                duration_ms=round((perf_counter() - start) * 1000, 2),
            )

            set_request_id(None)

            # asyncpg connections are loop-bound; each task gets its own asyncio.run loop,
            # so we must dispose the pool or the next task reuses a dead connection
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
