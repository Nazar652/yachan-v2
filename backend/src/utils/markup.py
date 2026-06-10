import re
from typing import cast

import mistune
from mistune.block_parser import BlockParser

# matches imageboard post references like >>123
_POST_REF_RE = re.compile(r">>(\d+)")
_POST_REF_PATTERN = r">>(?P<post_ref_num>\d+)"

# imageboard-style inline spoiler: %%hidden text%%. mistune's own spoiler plugin
# uses >!text!<, which collides with blockquote when placed at line start
_SPOILER_PATTERN = r"%%(?P<spoiler_text>[\s\S]+?)%%"

_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
# a zero-width space keeps an otherwise-empty line non-blank, so markdown does
# not collapse runs of blank lines into a single paragraph break; with hard_wrap
# each preserved line then renders as its own <br>, so the poster's exact spacing
# survives. code fences are skipped — their blank lines are literal content.
_BLANK_LINE_PLACEHOLDER = "​"


def preserve_blank_lines(text: str) -> str:
    lines = text.split("\n")
    fence_marker: str | None = None
    result: list[str] = []
    for line in lines:
        match = _FENCE_RE.match(line)
        if fence_marker is None:
            if match:
                fence_marker = match.group(1)
                result.append(line)
            elif line.strip() == "":
                result.append(_BLANK_LINE_PLACEHOLDER)
            else:
                result.append(line)
        else:
            if match and match.group(1)[0] == fence_marker[0] and len(match.group(1)) >= len(fence_marker):
                fence_marker = None
            result.append(line)
    return "\n".join(result)


def parse_post_ref(inline, match, state):
    state.append_token({"type": "post_ref", "raw": match.group("post_ref_num")})
    return match.end()


def render_post_ref(renderer, raw: str) -> str:
    return f'<a class="post-ref" data-post="{raw}">&gt;&gt;{raw}</a>'


def post_ref_plugin(md: mistune.Markdown) -> None:
    # the parameter must be named `md` to satisfy mistune's plugin protocol type
    md.inline.register("post_ref", _POST_REF_PATTERN, parse_post_ref, before="link")
    if md.renderer is not None and md.renderer.NAME == "html":
        md.renderer.register("post_ref", render_post_ref)


class _PostRefBlockParser(BlockParser):
    # a line starting with >>digits is an imageboard post reference, handled by
    # the inline post_ref plugin. the negative lookahead keeps it out of the
    # blockquote rule so it is not swallowed as greentext (which also pulled the
    # following line into the quote). plain >text greentext still matches.
    SPECIFICATION = {
        **BlockParser.SPECIFICATION,
        "block_quote": r"^ {0,3}>(?!>\d)(?P<quote_1>.*?)$",
    }


def parse_spoiler(inline, match, state):
    new_state = state.copy()
    new_state.src = match.group("spoiler_text")
    children = inline.render(new_state)
    state.append_token({"type": "spoiler", "children": children})
    return match.end()


def render_spoiler(renderer, text: str) -> str:
    return f'<span class="spoiler">{text}</span>'


def spoiler_plugin(md: mistune.Markdown) -> None:
    md.inline.register("spoiler", _SPOILER_PATTERN, parse_spoiler, before="link")
    if md.renderer is not None and md.renderer.NAME == "html":
        md.renderer.register("spoiler", render_spoiler)


class MarkupRenderer:
    """Renders raw post markdown into safe html (raw html is escaped)."""

    def __init__(self) -> None:
        self.markdown = mistune.create_markdown(
            escape=True,
            hard_wrap=True,
            plugins=["strikethrough", "insert", "url", spoiler_plugin, post_ref_plugin],
        )
        # swap in a block parser that leaves >>N references to the inline plugin;
        # our plugins are all inline, so the block rules are otherwise unchanged
        self.markdown.block = _PostRefBlockParser()

    def render(self, text: str) -> str:
        # markdown(text) returns str in html mode; the union also covers ast mode
        return cast(str, self.markdown(preserve_blank_lines(text)))


def extract_post_refs(text: str) -> list[int]:
    """Unique post numbers referenced via >>N, in order of first appearance."""
    seen: dict[int, None] = {}
    for match in _POST_REF_RE.finditer(text):
        seen.setdefault(int(match.group(1)), None)
    return list(seen)
