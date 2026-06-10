from src.utils.markup import MarkupRenderer, extract_post_refs


def test_renders_post_reference_as_link():
    html = MarkupRenderer().render("see >>123")
    assert 'data-post="123"' in html
    assert "post-ref" in html


def test_escapes_raw_html():
    html = MarkupRenderer().render("<script>alert(1)</script>")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_renders_basic_markdown():
    html = MarkupRenderer().render("**bold**")
    assert "<strong>bold</strong>" in html


def test_single_newline_becomes_line_break():
    html = MarkupRenderer().render("line one\nline two")
    assert "<br" in html
    assert "line one" in html
    assert "line two" in html


def test_blank_lines_are_preserved_exactly():
    one_blank = MarkupRenderer().render("a\n\nb")
    two_blanks = MarkupRenderer().render("a\n\n\nb")
    # every extra blank line survives as one more break instead of collapsing
    assert two_blanks.count("<br") == one_blank.count("<br") + 1


def test_code_block_blank_lines_stay_literal():
    html = MarkupRenderer().render("```\na\n\nb\n```")
    # blank lines inside a code fence are content, not spacing — no placeholder
    assert "​" not in html


def test_renders_underscore_italic():
    html = MarkupRenderer().render("_italic_")
    assert "<em>italic</em>" in html


def test_renders_underline():
    html = MarkupRenderer().render("^^underlined^^")
    assert "<ins>underlined</ins>" in html


def test_backslash_escapes_disable_markup():
    html = MarkupRenderer().render(r"\*\*not bold\*\* \%\%not spoiler\%\% \^\^not ins\^\^")
    assert "<strong>" not in html
    assert 'class="spoiler"' not in html
    assert "<ins>" not in html
    assert "**not bold** %%not spoiler%% ^^not ins^^" in html


def test_backslash_escapes_disable_post_ref():
    html = MarkupRenderer().render(r"\>>123")
    assert "post-ref" not in html


def test_renders_spoiler():
    html = MarkupRenderer().render("a %%hidden%% b")
    assert '<span class="spoiler">hidden</span>' in html


def test_renders_spoiler_at_line_start():
    html = MarkupRenderer().render("%%hidden%%")
    assert '<span class="spoiler">hidden</span>' in html
    assert "blockquote" not in html


def test_renders_nested_markup_inside_spoiler():
    html = MarkupRenderer().render("%%**bold** and `code`%%")
    assert '<span class="spoiler"><strong>bold</strong> and <code>code</code></span>' in html


def test_spoiler_spans_soft_line_break():
    html = MarkupRenderer().render("%%first\nsecond%%")
    assert '<span class="spoiler">' in html
    assert "second" in html


def test_escapes_raw_html_inside_spoiler():
    html = MarkupRenderer().render("%%<b>x</b>%%")
    assert "<b>" not in html
    assert "&lt;b&gt;" in html


def test_post_ref_at_line_start_is_a_link_not_a_blockquote():
    html = MarkupRenderer().render(">>26")
    assert 'data-post="26"' in html
    assert "blockquote" not in html


def test_post_ref_at_line_start_does_not_swallow_the_next_line():
    html = MarkupRenderer().render(">>26\nreply text")
    assert 'data-post="26"' in html
    assert "blockquote" not in html
    # the following line stays out of any quote, as ordinary paragraph text
    assert "reply text" in html


def test_greentext_at_line_start_still_renders_as_blockquote():
    html = MarkupRenderer().render(">greentext")
    assert "<blockquote>" in html
    assert "greentext" in html


def test_extract_post_refs_dedups_in_order():
    assert extract_post_refs("see >>10 and >>20 and >>10") == [10, 20]


def test_extract_post_refs_empty():
    assert extract_post_refs("no refs here") == []
