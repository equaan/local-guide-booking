from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Booking, BookingStatus, Slot, User, UserRole


def _make_slot() -> tuple[Slot, User, User]:
    guide = User(
        name="Guide",
        email="guide@example.com",
        password_hash="hash",
        role=UserRole.GUIDE,
        city="Mumbai",
    )
    first_traveler = User(
        name="Traveler One",
        email="traveler-one@example.com",
        password_hash="hash",
        role=UserRole.TRAVELER,
    )
    second_traveler = User(
        name="Traveler Two",
        email="traveler-two@example.com",
        password_hash="hash",
        role=UserRole.TRAVELER,
    )
    start_at = datetime(2030, 1, 1, 10, 0)
    slot = Slot(
        guide=guide,
        title="Walking tour",
        start_at=start_at,
        end_at=start_at + timedelta(hours=2),
    )
    db.session.add_all([guide, first_traveler, second_traveler, slot])
    db.session.commit()
    return slot, first_traveler, second_traveler


def test_database_rejects_second_confirmed_booking_for_slot(app) -> None:
    with app.app_context():
        slot, first_traveler, second_traveler = _make_slot()
        db.session.add(
            Booking(
                slot_id=slot.id,
                traveler_id=first_traveler.id,
                status=BookingStatus.CONFIRMED,
            )
        )
        db.session.commit()

        db.session.add(
            Booking(
                slot_id=slot.id,
                traveler_id=second_traveler.id,
                status=BookingStatus.CONFIRMED,
            )
        )
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_database_rejects_second_active_booking_for_same_traveler(app) -> None:
    with app.app_context():
        slot, first_traveler, _ = _make_slot()
        db.session.add(
            Booking(
                slot_id=slot.id,
                traveler_id=first_traveler.id,
                status=BookingStatus.PENDING,
            )
        )
        db.session.commit()

        db.session.add(
            Booking(
                slot_id=slot.id,
                traveler_id=first_traveler.id,
                status=BookingStatus.CONFIRMED,
            )
        )
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
