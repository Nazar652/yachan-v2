import pytest

from src.bootstrap.scope import (
    close_scope,
    current_scope,
    open_scope,
    resolve_scoped,
)


class Dummy:
    pass


@pytest.fixture(autouse=True)
def _clean_scope():
    close_scope()
    yield
    close_scope()


def test_open_and_close_scope():
    assert current_scope() is None
    open_scope()
    assert current_scope() == {}
    close_scope()
    assert current_scope() is None


def test_resolve_without_scope_calls_factory_every_time():
    calls = []

    def factory():
        calls.append(1)
        return Dummy()

    a = resolve_scoped(Dummy, factory)
    b = resolve_scoped(Dummy, factory)
    assert a is not b
    assert len(calls) == 2


def test_resolve_with_scope_caches_instance():
    open_scope()
    calls = []

    def factory():
        calls.append(1)
        return Dummy()

    a = resolve_scoped(Dummy, factory)
    b = resolve_scoped(Dummy, factory)
    assert a is b
    assert len(calls) == 1


def test_force_new_returns_fresh_and_does_not_cache():
    open_scope()
    cached = resolve_scoped(Dummy, Dummy)
    fresh = resolve_scoped(Dummy, Dummy, force_new=True)
    assert fresh is not cached
    # cache still holds the original instance
    assert resolve_scoped(Dummy, Dummy) is cached
