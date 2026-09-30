"""Centralised application time handling."""

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def now_ist() -> datetime:
    """Return naive IST time so container UTC cannot shift business rules."""
    return datetime.now(IST).replace(tzinfo=None)
