from src.utils.search_text import clean_search_text


def test_strips_post_refs():
    assert clean_search_text(">>25\nперевірка фіксу markup") == "перевірка фіксу markup"


def test_strips_markdown_markers():
    assert clean_search_text("**bold** ~~strike~~ %%spoiler%% `code`") == "bold strike spoiler code"


def test_collapses_whitespace():
    assert clean_search_text("a\n\n  b   c") == "a b c"


def test_plain_text_unchanged():
    assert clean_search_text("перевірка") == "перевірка"


def test_empty_stays_empty():
    assert clean_search_text("") == ""
