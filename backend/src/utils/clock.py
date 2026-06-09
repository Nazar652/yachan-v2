from datetime import UTC, datetime


def utcnow() -> datetime:
    # tz-aware utc; the timestamp columns are timestamptz, so the offset is
    # preserved end to end and clients receive an unambiguous instant
    return datetime.now(UTC)
