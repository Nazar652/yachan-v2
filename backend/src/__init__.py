from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.bootstrap.container import setup_di
from src.core.config import get_settings
from src.core.sentry import init_sentry
from src.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitedError,
    UnauthorizedError,
)
from src.middleware.scope import ScopeMiddleware
from src.routers import boards, captcha, mod, posts, reports, threads, ws


def create_app() -> FastAPI:
    setup_di()
    settings = get_settings()
    init_sentry(settings)

    app = FastAPI(title=settings.app_name, version=settings.app_version)
    # noinspection PyTypeChecker
    app.add_middleware(ScopeMiddleware)
    # added last so it wraps ScopeMiddleware: cors preflight is answered before
    # a db scope is opened
    # noinspection PyTypeChecker
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    @app.exception_handler(BadRequestError)
    async def _bad_request(request, exc: BadRequestError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(UnauthorizedError)
    async def _unauthorized(request, exc: UnauthorizedError):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    app.include_router(boards.router, prefix="/api")
    app.include_router(threads.router, prefix="/api")
    app.include_router(posts.router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    app.include_router(captcha.router, prefix="/api")
    app.include_router(mod.router, prefix="/api")
    app.include_router(ws.router, prefix="/api")

    return app
