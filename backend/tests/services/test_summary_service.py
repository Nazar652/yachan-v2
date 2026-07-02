from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from src.services.summary_service import (
    MAX_POSTS_IN_PROMPT,
    SummaryService,
    build_prompt,
    select_posts,
)


def post(number: int, body: str = "text"):
    return SimpleNamespace(post_number=number, body=body)


def build():
    thread_repo = MagicMock()
    thread_repo.set_summary = AsyncMock()
    post_repo = MagicMock()
    gemini = MagicMock()
    gemini.generate = AsyncMock(return_value="a tl;dr")
    events = MagicMock()
    events.publish = AsyncMock()
    service = SummaryService(
        thread_repo=thread_repo, post_repo=post_repo, gemini_client=gemini, events=events
    )
    return service, thread_repo, post_repo, gemini, events


async def test_summarize_writes_summary_and_publishes():
    service, thread_repo, post_repo, gemini, events = build()
    thread_repo.get_by_id = AsyncMock(
        return_value=SimpleNamespace(id=5, title="t", reply_count=30)
    )
    post_repo.get_thread_posts = AsyncMock(return_value=[post(i) for i in range(1, 15)])

    await service.summarize_thread(5)

    gemini.generate.assert_awaited_once()
    thread_repo.set_summary.assert_awaited_once_with(5, "a tl;dr", 30)
    events.publish.assert_awaited_once()


async def test_summarize_skips_missing_thread():
    service, thread_repo, post_repo, gemini, _ = build()
    thread_repo.get_by_id = AsyncMock(return_value=None)
    post_repo.get_thread_posts = AsyncMock()

    await service.summarize_thread(5)

    gemini.generate.assert_not_awaited()
    thread_repo.set_summary.assert_not_awaited()


async def test_summarize_skips_thread_below_threshold():
    service, thread_repo, post_repo, gemini, _ = build()
    thread_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(id=5, title="t", reply_count=2))
    post_repo.get_thread_posts = AsyncMock(return_value=[post(1), post(2)])

    await service.summarize_thread(5)

    gemini.generate.assert_not_awaited()
    thread_repo.set_summary.assert_not_awaited()


async def test_summarize_skips_empty_model_output():
    service, thread_repo, post_repo, gemini, events = build()
    thread_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(id=5, title="t", reply_count=30))
    post_repo.get_thread_posts = AsyncMock(return_value=[post(i) for i in range(1, 15)])
    gemini.generate = AsyncMock(return_value="")

    await service.summarize_thread(5)

    thread_repo.set_summary.assert_not_awaited()
    events.publish.assert_not_awaited()


async def test_stale_thread_ids_maps_ids():
    service, thread_repo, *_ = build()
    thread_repo.list_threads_needing_summary = AsyncMock(
        return_value=[SimpleNamespace(id=1), SimpleNamespace(id=2)]
    )

    assert await service.stale_thread_ids() == [1, 2]


def test_select_posts_caps_and_keeps_op():
    posts = [post(i) for i in range(1, 101)]
    kept = select_posts(posts)
    assert len(kept) == MAX_POSTS_IN_PROMPT
    assert kept[0].post_number == 1


def test_build_prompt_includes_title_and_bodies():
    prompt = build_prompt("My Title", [post(1, "hello"), post(2, "world")])
    assert "My Title" in prompt
    assert "hello" in prompt
    assert "world" in prompt
