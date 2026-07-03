import argparse
from unittest.mock import AsyncMock, MagicMock

from src.cli import embed_posts


def test_handle_indexes_all_and_reports(monkeypatch, capsys):
    service = MagicMock()
    service.index_all = AsyncMock(return_value=3)
    monkeypatch.setattr(embed_posts, "SearchService", lambda: service)

    async def fake_scope(work):
        return await work()

    monkeypatch.setattr(embed_posts, "run_in_scope", fake_scope)

    embed_posts.handle(argparse.Namespace())

    service.index_all.assert_awaited_once()
    assert "indexed 3 posts" in capsys.readouterr().out
