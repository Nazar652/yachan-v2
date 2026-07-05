from contextvars import ContextVar
from uuid import uuid4

# correlates one log trail across http middleware, outgoing calls and celery
# tasks; None means nothing set it (e.g. beat-triggered tasks with no request)
_request_id: ContextVar[str | None] = ContextVar("_request_id", default=None)


def new_id() -> str:
    return uuid4().hex


def set_request_id(value: str | None) -> None:
    _request_id.set(value)


def get_request_id() -> str | None:
    return _request_id.get()
