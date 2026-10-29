"""All timestamps are stored as naive UTC datetimes and serialised as ISO-8601 with a trailing Z."""
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_iso(dt):
    return dt.isoformat(timespec="seconds") + "Z" if dt else None


def parse_iso(value):
    """Parse an ISO-8601 string (optionally ending in Z / with offset) into naive UTC."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("empty datetime")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
