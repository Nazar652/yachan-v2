from src.core.markup import MarkupRenderer, extract_post_refs


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


def test_extract_post_refs_dedups_in_order():
    assert extract_post_refs("see >>10 and >>20 and >>10") == [10, 20]


def test_extract_post_refs_empty():
    assert extract_post_refs("no refs here") == []
