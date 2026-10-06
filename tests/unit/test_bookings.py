from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models import Booking, BookingEvent, BookingStatus, Slot, User, UserRole
from app.services.bookings import (
    BookingValidationError,
    cancel_booking,
    confirm_booking,
    request_booking,
)

NOW = datetime(2030, 1, 1, 9, 0)


def _make_data(
    *, started: bool = False, suffix: str = ""
) -> tuple[Slot, User, User, User]:
    guide = User(
        name="Guide",
        email=f"guide{suffix}@example.com",
        password_hash="hash",
        role=UserRole.GUIDE,
        city="Mumbai",
    )
    traveler_one = User(
        name="Traveler One",
        email=f"one{suffix}@example.com",
        password_hash="hash",
        role=UserRole.TRAVELER,
    )
    traveler_two = User(
        name="Traveler Two",
        email=f"two{suffix}@example.com",
        password_hash="hash",
        role=UserRole.TRAVELER,
    )
    start_at = NOW - timedelta(minutes=1) if started else NOW + timedelta(hours=1)
    slot = Slot(
        guide=guide,
        title="Walking tour",
        start_at=start_at,
        end_at=start_at + timedelta(hours=2),
    )
    db.session.add_all([guide, traveler_one, traveler_two, slot])
    db.session.commit()
    return slot, guide, traveler_one, traveler_two


def _events_for(booking: Booking) -> list[BookingEvent]:
    return list(
        db.session.scalars(
            db.select(BookingEvent)
            .where(BookingEvent.booking_id == booking.id)
            .order_by(BookingEvent.created_at)
        )
    )


def test_request_creates_pending_booking_and_event(app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        slot, _, traveler, _ = _make_data()

        booking = request_booking(slot.id, traveler.id, "Please reserve this.")

        assert booking.status is BookingStatus.PENDING
        assert booking.note == "Please reserve this."
        event = _events_for(booking)[0]
        assert (event.from_status, event.to_status, event.actor_id) == (
            None,
            BookingStatus.PENDING,
            traveler.id,
        )


def test_request_rejects_active_duplicate_and_started_slot(app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        slot, _, traveler, _ = _make_data()
        request_booking(slot.id, traveler.id)

        with pytest.raises(BookingValidationError, match="active booking"):
            request_booking(slot.id, traveler.id)

        started_slot, _, started_traveler, _ = _make_data(
            started=True, suffix="-started"
        )
        with pytest.raises(BookingValidationError, match="already started"):
            request_booking(started_slot.id, started_traveler.id)


def test_confirm_transitions_target_and_cancels_competitors(app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        slot, guide, traveler_one, traveler_two = _make_data()
        target = request_booking(slot.id, traveler_one.id)
        competitor = request_booking(slot.id, traveler_two.id)

        confirmed = confirm_booking(target.id, guide.id)
        db.session.refresh(competitor)

        assert confirmed.status is BookingStatus.CONFIRMED
        assert competitor.status is BookingStatus.CANCELLED
        assert [
            (event.to_status, event.reason) for event in _events_for(competitor)
        ] == [
            (BookingStatus.PENDING, None),
            (BookingStatus.CANCELLED, "slot taken"),
        ]


@pytest.mark.parametrize(
    "initial_status", [BookingStatus.PENDING, BookingStatus.CONFIRMED]
)
def test_cancel_records_transition_for_each_active_status(
    app, monkeypatch, initial_status: BookingStatus
) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        slot, guide, traveler, _ = _make_data()
        booking = request_booking(slot.id, traveler.id)
        if initial_status is BookingStatus.CONFIRMED:
            booking = confirm_booking(booking.id, guide.id)

        cancelled = cancel_booking(booking.id, traveler.id, "Plans changed")

        assert cancelled.status is BookingStatus.CANCELLED
        event = _events_for(cancelled)[-1]
        assert (event.from_status, event.to_status, event.actor_id, event.reason) == (
            initial_status,
            BookingStatus.CANCELLED,
            traveler.id,
            "Plans changed",
        )


def test_confirm_and_cancel_reject_invalid_actions(app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        slot, guide, traveler, other_traveler = _make_data()
        booking = request_booking(slot.id, traveler.id)

        with pytest.raises(BookingValidationError, match="slot's guide"):
            confirm_booking(booking.id, other_traveler.id)
        with pytest.raises(BookingValidationError, match="cannot cancel"):
            cancel_booking(booking.id, other_traveler.id)

        cancel_booking(booking.id, traveler.id)
        with pytest.raises(BookingValidationError, match="cannot be cancelled"):
            cancel_booking(booking.id, traveler.id)

        started_slot, started_guide, started_traveler, _ = _make_data(
            started=True, suffix="-started"
        )
        started_booking = Booking(
            slot_id=started_slot.id,
            traveler_id=started_traveler.id,
            status=BookingStatus.PENDING,
        )
        db.session.add(started_booking)
        db.session.commit()
        with pytest.raises(BookingValidationError, match="after the slot has started"):
            confirm_booking(started_booking.id, started_guide.id)
