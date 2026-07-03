from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from kink import di

import src.tasks.summary as summary_module
from src.services.summary_service import SummaryService
from src.tasks.summary import summarize_stale_threads, summarize_thread


def test_summarize_thread_delegates_to_service(monkeypatch):
    instance = MagicMock()
    instance.summarize_thread = AsyncMock()
    monkeypatch.setitem(di.factories, SummaryService, lambda container: instance)

    summarize_thread(5)

    instance.summarize_thread.assert_awaited_once_with(5)


def test_stale_threads_no_op_without_api_key(monkeypatch):
    instance = MagicMock()
    instance.stale_thread_ids = AsyncMock(return_value=[1, 2])
    monkeypatch.setitem(di.factories, SummaryService, lambda container: instance)
    monkeypatch.setattr(summary_module, "get_settings", lambda: SimpleNamespace(gemini_api_key=""))

    summarize_stale_threads()

    instance.stale_thread_ids.assert_not_awaited()


def test_stale_threads_enqueues_each_when_enabled(monkeypatch):
    instance = MagicMock()
    instance.stale_thread_ids = AsyncMock(return_value=[1, 2])
    monkeypatch.setitem(di.factories, SummaryService, lambda container: instance)
    monkeypatch.setattr(summary_module, "get_settings", lambda: SimpleNamespace(gemini_api_key="k"))
    delay = MagicMock()
    monkeypatch.setattr(summary_module.summarize_thread, "delay", delay)

    summarize_stale_threads()

    instance.stale_thread_ids.assert_awaited_once()
    assert delay.call_count == 2
    assert [call.args[0] for call in delay.call_args_list] == [1, 2]
