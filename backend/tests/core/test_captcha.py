from src.core.captcha import (
    _ALPHABET,
    generate_answer,
    new_token,
    render_image,
)


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
    data = render_image("ABC12")
    assert isinstance(data, bytes)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
