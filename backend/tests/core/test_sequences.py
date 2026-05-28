import pytest

from src.core.sequences import post_number_sequence_name


def test_valid_slug_builds_name():
    assert post_number_sequence_name("b") == "post_number_seq_b"
    assert post_number_sequence_name("vg_2") == "post_number_seq_vg_2"


@pytest.mark.parametrize(
    "bad",
    ["", "B", "has space", "drop;", "a" * 21, "слаг", "a-b"],
)
def test_invalid_slug_raises(bad):
    with pytest.raises(ValueError):
        post_number_sequence_name(bad)
