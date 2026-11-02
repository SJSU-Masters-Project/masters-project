from datetime import UTC, datetime


def utcnow() -> datetime:
    """Timezone-aware UTC now, truncated to millisecond precision (BSON keeps ms)."""
    now = datetime.now(UTC)
    return now.replace(microsecond=(now.microsecond // 1000) * 1000)


def to_iso(dt: datetime) -> str:
    """Render a datetime as ISO 8601 with millisecond precision ending in ``Z``.

    Example: ``2026-10-25T18:00:00.123Z``.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    dt = dt.astimezone(UTC)
    millis = dt.microsecond // 1000
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + f".{millis:03d}Z"
