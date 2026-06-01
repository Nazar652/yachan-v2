from kink import inject

from src.utils.markup import MarkupRenderer, extract_post_refs


@inject
class MarkupService:
    def __init__(self, renderer: MarkupRenderer) -> None:
        self.renderer = renderer

    def render(self, text: str | None) -> str | None:
        if not text:
            return None
        return self.renderer.render(text)

    def extract_refs(self, text: str | None) -> list[int]:
        if not text:
            return []
        return extract_post_refs(text)
