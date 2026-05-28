from datetime import UTC, datetime

from src.core.clock import utcnow


def test_utcnow_is_naive():
    now = utcnow()
    assert isinstance(now, datetime)
    assert now.tzinfo is None


def test_utcnow_close_to_real_utc():
    before = datetime.now(UTC).replace(tzinfo=None)
    now = utcnow()
    after = datetime.now(UTC).replace(tzinfo=None)
    assert before <= now <= after
