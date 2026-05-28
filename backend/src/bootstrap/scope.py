from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

# None means no active scope (startup, raw scripts)
_scope: ContextVar[dict[type, Any] | None] = ContextVar("_scope", default=None)


def open_scope() -> None:
    _scope.set({})


def close_scope() -> None:
    _scope.set(None)


def current_scope() -> dict[type, Any] | None:
    return _scope.get()


def resolve_scoped[T](
    cls: type[T],
    factory: Callable[..., T],
    *,
    force_new: bool = False,
) -> T:
    """
    Resolve a scoped instance.

    Behaviour:
      - active scope and cls already created: return cached instance
      - active scope and cls not yet created: call factory(), cache, return
      - no active scope: call factory() every time (no caching)
      - force_new=True: always call factory(); do not update the scope cache
    """
    scope = _scope.get()

    if scope is None or force_new:
        return factory()

    if cls not in scope:
        scope[cls] = factory()

    return scope[cls]
