from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models import Booking, BookingEvent, BookingStatus, Slot, User, UserRole
from app.services.slots import (
    SlotValidationError,
    create_slot,
    deactivate_slot,
    list_guide_slots,
    validate_slot_times,
)

FIXED_NOW = datetime(2030, 1, 1, 9, 0)


def _guide() -> User:
    guide = User(
        name="Guide",
        email="guide@example.com",
        password_hash="hash",
        role=UserRole.GUIDE,
        city="Mumbai",
    )
    db.session.add(guide)
    db.session.commit()
    return guide


def test_slot_time_rules_reject_past_and_invalid_durations() -> None:
    with pytest.raises(SlotValidationError, match="future"):
        validate_slot_times(
            FIXED_NOW, FIXED_NOW + timedelta(hours=1), current_time=FIXED_NOW
        )
    with pytest.raises(SlotValidationError, match="after"):
        validate_slot_times(
            FIXED_NOW + timedelta(hours=1),
            FIXED_NOW + timedelta(hours=1),
            current_time=FIXED_NOW,
        )
    with pytest.raises(SlotValidationError, match="30 minutes"):
        validate_slot_times(
            FIXED_NOW + timedelta(hours=1),
            FIXED_NOW + timedelta(hours=1, minutes=29),
            current_time=FIXED_NOW,
        )
    with pytest.raises(SlotValidationError, match="12 hours"):
        validate_slot_times(
            FIXED_NOW + timedelta(hours=1),
            FIXED_NOW + timedelta(hours=13, minutes=1),
            current_time=FIXED_NOW,
        )


def test_create_slot_rejects_overlap_and_negative_price(app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    with app.app_context():
        guide = _guide()
        create_slot(
            guide.id,
            "Morning walk",
            FIXED_NOW + timedelta(hours=1),
            FIXED_NOW + timedelta(hours=3),
            500,
        )
        with pytest.raises(SlotValidationError, match="overlaps"):
            create_slot(
                guide.id,
                "Overlap",
                FIXED_NOW + timedelta(hours=2),
                FIXED_NOW + timedelta(hours=4),
                500,
            )
        with pytest.raises(SlotValidationError, match="negative"):
            create_slot(
                guide.id,
                "Negative",
                FIXED_NOW + timedelta(hours=4),
                FIXED_NOW + timedelta(hours=5),
                -1,
            )


def test_list_derives_available_booked_inactive_and_past_statuses(
    app, monkeypatch
) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    with app.app_context():
        guide = _guide()
        create_slot(
            guide.id,
            "Available",
            FIXED_NOW + timedelta(hours=1),
            FIXED_NOW + timedelta(hours=2),
            0,
        )
        booked = create_slot(
            guide.id,
            "Booked",
            FIXED_NOW + timedelta(hours=3),
            FIXED_NOW + timedelta(hours=4),
            0,
        )
        inactive = create_slot(
            guide.id,
            "Inactive",
            FIXED_NOW + timedelta(hours=5),
            FIXED_NOW + timedelta(hours=6),
            0,
        )
        past = Slot(
            guide_id=guide.id,
            title="Past",
            start_at=FIXED_NOW - timedelta(hours=2),
            end_at=FIXED_NOW - timedelta(hours=1),
            price_inr=0,
        )
        traveler = User(
            name="Traveler",
            email="traveler@example.com",
            password_hash="hash",
            role=UserRole.TRAVELER,
        )
        db.session.add_all(
            [
                past,
                Booking(slot=booked, traveler=traveler, status=BookingStatus.CONFIRMED),
            ]
        )
        inactive.is_active = False
        db.session.commit()

        statuses = dict(
            (slot.title, status) for slot, status in list_guide_slots(guide.id)
        )
        assert statuses == {
            "Past": "past",
            "Available": "available",
            "Booked": "booked",
            "Inactive": "inactive",
        }


def test_deactivate_cancels_pending_booking_and_records_system_event(
    app, monkeypatch
) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    with app.app_context():
        guide = _guide()
        traveler = User(
            name="Traveler",
            email="traveler@example.com",
            password_hash="hash",
            role=UserRole.TRAVELER,
        )
        slot = Slot(
            guide_id=guide.id,
            title="Walk",
            start_at=FIXED_NOW + timedelta(hours=1),
            end_at=FIXED_NOW + timedelta(hours=2),
            price_inr=0,
        )
        booking = Booking(slot=slot, traveler=traveler, status=BookingStatus.PENDING)
        db.session.add_all([slot, traveler, booking])
        db.session.commit()

        deactivate_slot(slot)

        assert slot.is_active is False
        assert booking.status is BookingStatus.CANCELLED
        event = db.session.scalar(
            db.select(BookingEvent).where(BookingEvent.booking_id == booking.id)
        )
        assert event is not None
        assert event.actor_id is None
        assert event.reason == "slot deactivated"


def test_deactivate_rejects_confirmed_slot(app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    with app.app_context():
        guide = _guide()
        traveler = User(
            name="Traveler",
            email="confirmed-traveler@example.com",
            password_hash="hash",
            role=UserRole.TRAVELER,
        )
        slot = Slot(
            guide_id=guide.id,
            title="Confirmed walk",
            start_at=FIXED_NOW + timedelta(hours=1),
            end_at=FIXED_NOW + timedelta(hours=2),
            price_inr=0,
        )
        db.session.add_all(
            [
                slot,
                traveler,
                Booking(slot=slot, traveler=traveler, status=BookingStatus.CONFIRMED),
            ]
        )
        db.session.commit()

        with pytest.raises(SlotValidationError, match="confirmed booking"):
            deactivate_slot(slot)
