from contextvars import ContextVar
from typing import Any
from collections.abc import Callable

from kink import Container
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_request_container: ContextVar[Container] = ContextVar("request_container")


def request_scoped(dependency_class: Any) -> Callable[[], Any]:
    """
    Creates a factory function for request-scoped dependency injection.

    Registers a lazy factory on the kink Container stored in the current
    request's ContextVar.  The factory is called at most once per request —
    kink caches the result inside the Container instance so subsequent calls
    within the same request return the same object.

    Args:
        dependency_class: The class type of the dependency to be instantiated.

    Returns:
        A factory function that returns an instance of the dependency class.
        The returned instance is scoped to the current request.

    Example:
        di.factories[Service] = request_scoped(Service)
    """
    def return_dependency() -> Any:
        container = _request_container.get()

        if dependency_class not in container:
            # Register a kink factory so the container owns instantiation
            # and caches the result for the lifetime of this request.
            container[dependency_class] = lambda di: dependency_class()

        return container[dependency_class]

    return return_dependency


def setup_container() -> None:
    """Initialise a fresh kink Container for the current request context."""
    _request_container.set(Container())


class ContainerMiddleware(BaseHTTPMiddleware):
    """Middleware that initialises a fresh kink DI container for every request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        setup_container()
        return await call_next(request)
