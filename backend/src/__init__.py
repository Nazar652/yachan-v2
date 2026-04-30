from fastapi import FastAPI

from src.lifespans import lifespan


def create_app() -> FastAPI:
    app = FastAPI(title="yachan-v2 API", version="0.1.0", lifespan=lifespan)

    return app
