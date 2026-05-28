from sqlalchemy.ext.asyncio import AsyncSession
from starlette.types import ASGIApp, Receive, Scope, Send

from src.bootstrap.scope import close_scope, current_scope, open_scope


class ScopeMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        open_scope()
        try:
            await self.app(scope, receive, send)
            await self._commit()
        except Exception:
            await self._rollback()
            raise
        finally:
            await self._close()
            close_scope()

    @staticmethod
    async def _session() -> AsyncSession | None:
        scope = current_scope()
        return scope.get(AsyncSession) if scope else None

    async def _commit(self) -> None:
        if session := await self._session():
            await session.commit()

    async def _rollback(self) -> None:
        if session := await self._session():
            await session.rollback()

    async def _close(self) -> None:
        if session := await self._session():
            await session.close()
