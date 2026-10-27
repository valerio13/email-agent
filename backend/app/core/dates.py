"""Date helpers shared by the services."""

from datetime import UTC, date, datetime


def utc_day(value: datetime) -> date:
    """Return the UTC calendar day of a datetime. Naive values are taken to be UTC already."""
    # SQLite gives back naive datetimes, while PostgreSQL gives back timezone-aware ones.
    if value.tzinfo is None:
        return value.date()
    return value.astimezone(UTC).date()
