from unittest.mock import MagicMock

from src.services.markup_service import MarkupService


def test_render_none_returns_none():
    renderer = MagicMock()
    service = MarkupService(renderer=renderer)

    assert service.render(None) is None
    assert service.render("") is None
    renderer.render.assert_not_called()


def test_render_delegates_to_renderer():
    renderer = MagicMock()
    renderer.render.return_value = "<p>hi</p>"
    service = MarkupService(renderer=renderer)

    assert service.render("hi") == "<p>hi</p>"
    renderer.render.assert_called_once_with("hi")


def test_extract_refs_empty_for_blank():
    service = MarkupService(renderer=MagicMock())
    assert service.extract_refs(None) == []
    assert service.extract_refs("") == []


def test_extract_refs_returns_numbers():
    service = MarkupService(renderer=MagicMock())
    assert service.extract_refs("see >>10 and >>20") == [10, 20]
