from datetime import UTC, datetime

from src.utils.clock import utcnow


def test_utcnow_is_aware_utc():
    now = utcnow()
    assert isinstance(now, datetime)
    assert now.tzinfo is UTC


def test_utcnow_close_to_real_utc():
    before = datetime.now(UTC)
    now = utcnow()
    after = datetime.now(UTC)
    assert before <= now <= after
