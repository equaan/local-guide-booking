"""Booking state transitions and their database-backed business rules."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import timeutils
from app.extensions import db
from app.metrics import record_booking_transition
from app.models import Booking, BookingEvent, BookingStatus, Slot


class BookingValidationError(ValueError):
    """Raised when an attempted transition breaks a booking business rule."""


def _slot_has_started(slot: Slot) -> bool:
    return slot.start_at <= timeutils.now_ist()


def _get_slot(slot_id: int) -> Slot:
    slot = db.session.scalar(select(Slot).where(Slot.id == slot_id))
    if slot is None:
        raise BookingValidationError("Slot not found.")
    return slot


def _get_booking(booking_id: int) -> Booking:
    booking = db.session.scalar(select(Booking).where(Booking.id == booking_id))
    if booking is None:
        raise BookingValidationError("Booking not found.")
    return booking


def _ensure_slot_is_bookable(slot: Slot) -> None:
    if not slot.is_active:
        raise BookingValidationError("This slot is no longer available.")
    if _slot_has_started(slot):
        raise BookingValidationError("Cannot book a slot that has already started.")
    confirmed_booking = db.session.scalar(
        select(Booking.id).where(
            Booking.slot_id == slot.id,
            Booking.status == BookingStatus.CONFIRMED,
        )
    )
    if confirmed_booking is not None:
        raise BookingValidationError("This slot is no longer available.")


def request_booking(slot_id: int, traveler_id: int, note: str | None = None) -> Booking:
    """Record a request and its event together so the timeline is never incomplete."""
    slot = _get_slot(slot_id)
    _ensure_slot_is_bookable(slot)

    active_booking = db.session.scalar(
        select(Booking.id).where(
            Booking.slot_id == slot_id,
            Booking.traveler_id == traveler_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        )
    )
    if active_booking is not None:
        raise BookingValidationError(
            "You already have an active booking for this slot."
        )

    booking = Booking(
        slot_id=slot_id,
        traveler_id=traveler_id,
        status=BookingStatus.PENDING,
        note=note.strip() if note else None,
    )
    db.session.add(booking)
    db.session.flush()
    db.session.add(
        BookingEvent(
            booking_id=booking.id,
            from_status=None,
            to_status=BookingStatus.PENDING,
            actor_id=traveler_id,
        )
    )
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise BookingValidationError("Could not create the booking request.") from error
    record_booking_transition(None, BookingStatus.PENDING)
    return booking


def confirm_booking(booking_id: int, guide_id: int) -> Booking:
    """Confirm one request while atomically cancelling every competing request."""
    booking = _get_booking(booking_id)
    slot = _get_slot(booking.slot_id)
    if booking.status is not BookingStatus.PENDING:
        raise BookingValidationError("Only PENDING bookings can be confirmed.")
    if slot.guide_id != guide_id:
        raise BookingValidationError("Only the slot's guide can confirm this booking.")
    if _slot_has_started(slot):
        raise BookingValidationError(
            "Cannot confirm a booking after the slot has started."
        )

    competing_bookings = db.session.scalars(
        select(Booking).where(
            Booking.slot_id == slot.id,
            Booking.id != booking.id,
            Booking.status == BookingStatus.PENDING,
        )
    ).all()

    booking.status = BookingStatus.CONFIRMED
    db.session.add(
        BookingEvent(
            booking_id=booking.id,
            from_status=BookingStatus.PENDING,
            to_status=BookingStatus.CONFIRMED,
            actor_id=guide_id,
        )
    )
    for competing_booking in competing_bookings:
        competing_booking.status = BookingStatus.CANCELLED
        db.session.add(
            BookingEvent(
                booking_id=competing_booking.id,
                from_status=BookingStatus.PENDING,
                to_status=BookingStatus.CANCELLED,
                actor_id=None,
                reason="slot taken",
            )
        )

    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise BookingValidationError("Could not confirm the booking.") from error
    record_booking_transition(BookingStatus.PENDING, BookingStatus.CONFIRMED)
    for _ in competing_bookings:
        record_booking_transition(BookingStatus.PENDING, BookingStatus.CANCELLED)
    return booking


def cancel_booking(
    booking_id: int, actor_id: int, reason: str | None = None
) -> Booking:
    """Cancel an active booking while retaining the event needed for its history."""
    booking = _get_booking(booking_id)
    slot = _get_slot(booking.slot_id)
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        raise BookingValidationError("This booking cannot be cancelled.")
    if booking.traveler_id != actor_id and slot.guide_id != actor_id:
        raise BookingValidationError("You cannot cancel this booking.")
    if _slot_has_started(slot):
        raise BookingValidationError(
            "Cannot cancel a booking after the slot has started."
        )

    previous_status = booking.status
    booking.status = BookingStatus.CANCELLED
    db.session.add(
        BookingEvent(
            booking_id=booking.id,
            from_status=previous_status,
            to_status=BookingStatus.CANCELLED,
            actor_id=actor_id,
            reason=reason.strip() if reason else None,
        )
    )
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise BookingValidationError("Could not cancel the booking.") from error
    record_booking_transition(previous_status, BookingStatus.CANCELLED)
    return booking
