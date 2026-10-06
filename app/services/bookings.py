"""Booking state machine service.

All booking state transitions and rules live in this module.
Routes should be thin: parse input, call a service function, choose response.
Every state change plus its booking_events row is wrapped in one transaction.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import timeutils
from app.extensions import db
from app.models import Booking, BookingEvent, BookingStatus, Slot, User


class BookingValidationError(ValueError):
    """Raised when a booking operation violates a rule."""


# ---------------------------------------------------------------------------
# BR-06: No booking action allowed once the slot has started
# ---------------------------------------------------------------------------

def _slot_has_started(slot: Slot) -> bool:
    """Return True if the slot's start time has already passed."""
    return slot.start_at <= timeutils.now_ist()


# ---------------------------------------------------------------------------
# BR-04: At most one CONFIRMED booking per slot (database enforced)
# BR-05: A traveler cannot hold two active bookings for the same slot
# -------------------------------------------------------------------------


def _check_traveler_active_booking(traveler_id: int, slot_id: int) -> None:
    """Raise if the traveler already has an active (PENDING / CONFIRMED) booking on this slot."""
    active = db.session.scalar(
        select(Booking).where(
            Booking.slot_id == slot_id,
            Booking.traveler_id == traveler_id,
            Booking.status.in_(("PENDING", "CONFIRMED")),
        )
    )
    if active is not None:
        raise BookingValidationError(
            "Traveler already has an active booking on this slot."
        )


# ---------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------


def request_booking(slot_id: int, traveler_id: int, note: str | None = None) -> Booking:
    """Request a booking for a slot.

    The booking starts as PENDING.  Raises BookingValidationError if:
      - the slot has already started (BR-06)
      - the traveler already has an active booking on this slot (BR-05)
      - the slot has no available capacity (BR-04 partial check via unique index)
    The returned booking is in PENDING state with one booking_events row.
    """
    slot = db.session.scalar(select(Slot).where(Slot.id == slot_id))
    if slot is None:
        raise BookingValidationError("Slot not found.")
    if _slot_has_started(slot):
        raise BookingValidationError("Cannot book a slot that has already started.")
    _check_traveler_active_booking(traveler_id, slot_id)

    # Begin transaction: status change + event row
    from sqlalchemy import text as sa_text

    booking = Booking(
        slot_id=slot_id,
        traveler_id=traveler_id,
        status=BookingStatus.PENDING,
        note=note,
    )
    db.session.add(booking)
    db.session.flush()  # assign booking.id

    event = BookingEvent(
        booking_id=booking.id,
        from_status=None,
        to_status=BookingStatus.PENDING,
        actor_id=None,
        reason="request",
    )
    db.session.add(event)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        # Re-raise as validation error if it's the partial unique index
        raise BookingValidationError("Could not create booking.") from exc

    return booking


def confirm_booking(booking_id: int, guide_id: int) -> Booking:
    """Confirm a PENDING booking.

    The guide who owns the slot changes the status to CONFIRMED.
    All other PENDING bookings on the same slot are auto-cancelled (BR-04
    / BR-07).  Raises BookingValidationError if:
      - the booking is not PENDING
      - the guide is not the slot's guide
      - the slot has already started (BR-06)
    The returned booking is in CONFIRMED state with one booking_events row.
    Other cancelled PENDING bookings also get one event row each.
    """
    booking = db.session.scalar(
        select(Booking).where(Booking.id == booking_id)
    )
    if booking is None:
        raise BookingValidationError("Booking not found.")
    if booking.status != BookingStatus.PENDING:
        raise BookingValidationError("Only PENDING bookings can be confirmed.")
    if booking.traveler is None:
        raise BookingValidationError("Booking has no traveler.")

    slot = db.session.scalar(select(Slot).where(Slot.id == booking.slot_id))
    if slot is None:
        raise BookingValidationError("Slot not found.")
    if _slot_has_started(slot):
        raise BookingValidationError("Cannot confirm a booking for a slot that has already started.")
    if slot.guide_id != guide_id:
        raise BookingValidationError("Only the guide who owns the slot can confirm.")

    # Auto-cancel competing PENDING bookings on the same slot (BR-04)
    competing = db.session.scalars(
        select(Booking).where(
            Booking.slot_id == slot_id,
            Booking.id != booking_id,
            Booking.status == BookingStatus.PENDING,
        )
    ).all()

    # Transition the target booking to CONFIRMED
    booking.status = BookingStatus.CONFIRMED

    # Cancel competing bookings
    for comp in competing:
        comp.status = BookingStatus.CANCELLED
        comp_event = BookingEvent(
            booking_id=comp.id,
            from_status=BookingStatus.PENDING,
            to_status=BookingStatus.CANCELLED,
            actor_id=None,
            reason="slot taken",
        )
        db.session.add(comp_event)

    # Event for the confirmed booking
    confirm_event = BookingEvent(
        booking_id=booking.id,
        from_status=BookingStatus.PENDING,
        to_status=BookingStatus.CONFIRMED,
        actor_id=guide_id,
        reason="confirmed",
    )
    db.session.add(confirm_event)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise BookingValidationError("Could not confirm booking.")

    return booking


def cancel_booking(booking_id: int, user_id: int, role: str | None = None, reason: str | None = None) -> Booking:
    """Cancel a PENDING or CONFIRMED booking.

    The booking's traveler or the slot's guide can cancel.
    - PENDING cancellations are simple.
    - CONFIRMED cancellations free the slot (it becomes available again).
    Raises BookingValidationError if:
      - the booking is not in a cancelable state
      - the user is not the traveler or the guide (BR-07 authorisation)
      - the slot has already started (BR-06)
    """
    booking = db.session.scalar(
        select(Booking).where(Booking.id == booking_id)
    )
    if booking is None:
        raise BookingValidationError("Booking not found.")

    slot = db.session.scalar(select(Slot).where(Slot.id == booking.slot_id))
    if slot is None:
        raise BookingValidationError("Slot not found.")
    if _slot_has_started(slot):
        raise BookingValidationError("Cannot cancel a booking for a slot that has already started.")

    # Ownership / role check (BR-07)
    is_traveler = booking.traveler_id == user_id
    is_guide = slot.guide_id == user_id

    if not is_traveler and not is_guide:
        raise BookingValidationError("You are not allowed to cancel this booking.")

    # Determine new status
    if booking.status == BookingStatus.PENDING:
        booking.status = BookingStatus.CANCELLED
        event = BookingEvent(
            booking_id=booking.id,
            from_status=BookingStatus.PENDING,
            to_status=BookingStatus.CANCELLED,
            actor_id=user_id,
            reason=reason or "cancelled",
        )
    elif booking.status == BookingStatus.CONFIRMED:
        booking.status = BookingStatus.CANCELLED
        # Slot becomes available again — no other action needed here;
        # the partial unique index (BR-04) will allow new bookings.
        event = BookingEvent(
            booking_id=booking.id,
            from_status=BookingStatus.CONFIRMED,
            to_status=BookingStatus.CANCELLED,
            actor_id=user_id,
            reason=reason or "cancelled",
        )
    else:
        raise BookingValidationError("Booking is in a state that cannot be cancelled.")

    db.session.add(event)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise BookingValidationError("Could not cancel booking.")

    return booking