import re
from typing import cast

import mistune

# matches imageboard post references like >>123
_POST_REF_RE = re.compile(r">>(\d+)")
_POST_REF_PATTERN = r">>(?P<post_ref_num>\d+)"


def _parse_post_ref(inline, match, state):
    state.append_token({"type": "post_ref", "raw": match.group("post_ref_num")})
    return match.end()


def _render_post_ref(renderer, raw: str) -> str:
    return f'<a class="post-ref" data-post="{raw}">&gt;&gt;{raw}</a>'


def _post_ref_plugin(md: mistune.Markdown) -> None:
    # the parameter must be named `md` to satisfy mistune's plugin protocol type
    md.inline.register("post_ref", _POST_REF_PATTERN, _parse_post_ref, before="link")
    if md.renderer is not None and md.renderer.NAME == "html":
        md.renderer.register("post_ref", _render_post_ref)


class MarkupRenderer:
    """Renders raw post markdown into safe html (raw html is escaped)."""

    def __init__(self) -> None:
        self.markdown = mistune.create_markdown(
            escape=True,
            plugins=["strikethrough", "url", _post_ref_plugin],
        )

    def render(self, text: str) -> str:
        # markdown(text) returns str in html mode; the union also covers ast mode
        return cast(str, self.markdown(text))


def extract_post_refs(text: str) -> list[int]:
    """Unique post numbers referenced via >>N, in order of first appearance."""
    seen: dict[int, None] = {}
    for match in _POST_REF_RE.finditer(text):
        seen.setdefault(int(match.group(1)), None)
    return list(seen)
