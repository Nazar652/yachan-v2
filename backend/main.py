from fastapi import FastAPI

from src.api import router


def create_app() -> FastAPI:
    app = FastAPI(title="yachan-v2 API", version="0.1.0")
    app.include_router(router)
    return app


application = create_app()

