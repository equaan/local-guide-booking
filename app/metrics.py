"""Prometheus instruments and helpers kept independent of request routes."""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
from sqlalchemy import func, select

from app.extensions import db
from app.models import Booking, BookingStatus

registry = CollectorRegistry()
http_requests = Counter(
    "lgb_http_requests",
    "HTTP requests handled by the application.",
    ("method", "endpoint", "status"),
    registry=registry,
)
http_request_duration = Histogram(
    "lgb_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("endpoint",),
    registry=registry,
)
booking_transitions = Counter(
    "lgb_bookings_transitions",
    "Booking state transitions.",
    ("from_status", "to_status"),
    registry=registry,
)
users_registered = Counter(
    "lgb_users_registered",
    "Users registered by role.",
    ("role",),
    registry=registry,
)
slots_created = Counter(
    "lgb_slots_created",
    "Slots successfully created.",
    registry=registry,
)
bookings_current = Gauge(
    "lgb_bookings_current",
    "Current bookings grouped by status.",
    ("status",),
    registry=registry,
)


def record_booking_transition(
    from_status: BookingStatus | None, to_status: BookingStatus
) -> None:
    """Count only transitions that have committed successfully."""
    booking_transitions.labels(
        from_status=from_status.value if from_status else "NONE",
        to_status=to_status.value,
    ).inc()


def refresh_bookings_current() -> None:
    """Compute booking counts at scrape time to avoid stale gauge values."""
    bookings_current.clear()
    statement = select(Booking.status, func.count(Booking.id)).group_by(Booking.status)
    for status, count in db.session.execute(statement):
        bookings_current.labels(status=status.value).set(count)
