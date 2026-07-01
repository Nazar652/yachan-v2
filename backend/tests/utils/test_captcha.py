from src.utils.captcha import (
    _ALPHABET,
    generate_answer,
    new_token,
    render_image,
    render_image_pair,
)

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def test_new_token_is_unique_hex():
    a, b = new_token(), new_token()
    assert a != b
    assert len(a) == 32
    assert all(c in "0123456789abcdef" for c in a)


def test_generate_answer_length_and_alphabet():
    answer = generate_answer(6)
    assert len(answer) == 6
    assert all(c in _ALPHABET for c in answer)


def test_render_image_returns_png_bytes():
    data = render_image("ABC12", "#ffffff", "#000000")
    assert isinstance(data, bytes)
    assert data[:8] == _PNG_MAGIC


def test_render_image_pair_returns_distinct_light_and_dark_png_bytes():
    light_image, dark_image = render_image_pair("ABC12")
    assert light_image[:8] == _PNG_MAGIC
    assert dark_image[:8] == _PNG_MAGIC
    assert light_image != dark_image
