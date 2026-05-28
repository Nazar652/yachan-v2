from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.bootstrap.container import setup_di
from src.core.config import get_settings
from src.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitedError,
)
from src.middleware.scope import ScopeMiddleware


def create_app() -> FastAPI:
    setup_di()
    settings = get_settings()

    app = FastAPI(title=settings.app_name, version=settings.app_version)
    # noinspection PyTypeChecker
    app.add_middleware(ScopeMiddleware)

    @app.exception_handler(NotFoundError)
    async def _not_found(request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def _forbidden(request, exc: ForbiddenError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def _conflict(request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(RateLimitedError)
    async def _rate_limited(request, exc: RateLimitedError):
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    return app
