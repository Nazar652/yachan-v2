from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.bootstrap.scope import close_scope, current_scope, open_scope


async def run_in_scope[T](work: Callable[[], Awaitable[T]]) -> T:
    """Run an async unit of work inside a di scope, committing on success and
    rolling back on error — the same lifecycle as the http middleware."""
    open_scope()

    try:
        result = await work()
        await _commit()
        return result
    except Exception:
        await _rollback()
        raise
    finally:
        await _close()
        close_scope()


def _session() -> AsyncSession | None:
    scope = current_scope()
    return scope.get(AsyncSession) if scope else None


async def _commit() -> None:
    if session := _session():
        await session.commit()


async def _rollback() -> None:
    if session := _session():
        await session.rollback()


async def _close() -> None:
    if session := _session():
        await session.close()
