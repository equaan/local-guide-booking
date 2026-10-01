from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import and_, select

from app import timeutils
from app.extensions import db
from app.models import BookingEvent, BookingStatus, Slot


class SlotValidationError(ValueError):
    """Raised when a slot violates a guide availability rule."""


def validate_slot_times(
    start_at: datetime, end_at: datetime, *, current_time: datetime | None = None
) -> None:
    """Validate future start and the permitted 30-minute to 12-hour duration."""
    now = current_time or timeutils.now_ist()
    duration = end_at - start_at
    if start_at <= now:
        raise SlotValidationError("Slot start time must be in the future.")
    if end_at <= start_at:
        raise SlotValidationError("Slot end time must be after its start time.")
    if duration < timedelta(minutes=30) or duration > timedelta(hours=12):
        raise SlotValidationError(
            "Slot duration must be between 30 minutes and 12 hours."
        )


def create_slot(
    guide_id: int,
    title: str,
    start_at: datetime,
    end_at: datetime,
    price_inr: int,
) -> Slot:
    """Create an active slot only when it does not overlap another active slot."""
    validate_slot_times(start_at, end_at)
    if price_inr < 0:
        raise SlotValidationError("Price cannot be negative.")

    overlap = db.session.scalar(
        select(Slot.id).where(
            Slot.guide_id == guide_id,
            Slot.is_active.is_(True),
            and_(Slot.start_at < end_at, Slot.end_at > start_at),
        )
    )
    if overlap is not None:
        raise SlotValidationError("Slot overlaps another active slot.")

    slot = Slot(
        guide_id=guide_id,
        title=title.strip(),
        start_at=start_at,
        end_at=end_at,
        price_inr=price_inr,
    )
    db.session.add(slot)
    db.session.commit()
    return slot


def list_guide_slots(guide_id: int) -> list[tuple[Slot, str]]:
    """Return a guide's slots with the status required by the guide view."""
    current_time = timeutils.now_ist()
    slots = db.session.scalars(
        select(Slot).where(Slot.guide_id == guide_id).order_by(Slot.start_at.asc())
    ).all()
    result = []
    for slot in slots:
        if not slot.is_active:
            status = "inactive"
        elif slot.start_at <= current_time:
            status = "past"
        elif any(
            booking.status is BookingStatus.CONFIRMED for booking in slot.bookings
        ):
            status = "booked"
        else:
            status = "available"
        result.append((slot, status))
    return result


def deactivate_slot(slot: Slot) -> None:
    """Deactivate an unconfirmed slot and record system cancellations atomically."""
    if any(booking.status is BookingStatus.CONFIRMED for booking in slot.bookings):
        raise SlotValidationError(
            "A slot with a confirmed booking cannot be deactivated."
        )

    slot.is_active = False
    for booking in slot.bookings:
        if booking.status is BookingStatus.PENDING:
            booking.status = BookingStatus.CANCELLED
            db.session.add(
                BookingEvent(
                    booking_id=booking.id,
                    from_status=BookingStatus.PENDING,
                    to_status=BookingStatus.CANCELLED,
                    actor_id=None,
                    reason="slot deactivated",
                )
            )
    db.session.commit()
