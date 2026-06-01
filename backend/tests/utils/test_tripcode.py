from src.utils.tripcode import compute_tripcode


def test_starts_with_bang_and_has_expected_length():
    trip = compute_tripcode("secret")
    assert trip.startswith("!")
    assert len(trip) == 11  # "!" + 10 chars


def test_is_deterministic():
    assert compute_tripcode("secret") == compute_tripcode("secret")


def test_different_passwords_differ():
    assert compute_tripcode("a") != compute_tripcode("b")


def test_has_no_url_unsafe_chars():
    trip = compute_tripcode("some+random/password=value")
    assert "+" not in trip[1:]
    assert "/" not in trip[1:]
