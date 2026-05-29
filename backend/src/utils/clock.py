from datetime import UTC, datetime


def utcnow() -> datetime:
    # naive utc to match the timestamp-without-tz columns; asyncpg rejects
    # tz-aware values for those columns
    return datetime.now(UTC).replace(tzinfo=None)
