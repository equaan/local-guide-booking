from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models import Booking, BookingStatus, Slot, User, UserRole
from app.services.slots import list_public_slots

FIXED_NOW = datetime(2030, 1, 1, 9, 0)


def test_public_slot_query_applies_filters_and_exclusions(app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    with app.app_context():
        mumbai_guide = User(
            name="Mumbai Guide",
            email="mumbai@example.com",
            password_hash="hash",
            role=UserRole.GUIDE,
            city="Mumbai",
        )
        delhi_guide = User(
            name="Delhi Guide",
            email="delhi@example.com",
            password_hash="hash",
            role=UserRole.GUIDE,
            city="Delhi",
        )
        traveler = User(
            name="Traveler",
            email="public-traveler@example.com",
            password_hash="hash",
            role=UserRole.TRAVELER,
        )
        visible_early = Slot(
            guide=mumbai_guide,
            title="Early Mumbai",
            start_at=FIXED_NOW + timedelta(days=1, hours=1),
            end_at=FIXED_NOW + timedelta(days=1, hours=2),
            price_inr=500,
        )
        visible_late = Slot(
            guide=mumbai_guide,
            title="Late Mumbai",
            start_at=FIXED_NOW + timedelta(days=1, hours=3),
            end_at=FIXED_NOW + timedelta(days=1, hours=4),
            price_inr=700,
        )
        other_city = Slot(
            guide=delhi_guide,
            title="Delhi Walk",
            start_at=FIXED_NOW + timedelta(days=1, hours=2),
            end_at=FIXED_NOW + timedelta(days=1, hours=3),
            price_inr=600,
        )
        past = Slot(
            guide=mumbai_guide,
            title="Past",
            start_at=FIXED_NOW - timedelta(hours=2),
            end_at=FIXED_NOW - timedelta(hours=1),
            price_inr=0,
        )
        inactive = Slot(
            guide=mumbai_guide,
            title="Inactive",
            start_at=FIXED_NOW + timedelta(days=1, hours=5),
            end_at=FIXED_NOW + timedelta(days=1, hours=6),
            price_inr=0,
            is_active=False,
        )
        confirmed = Slot(
            guide=mumbai_guide,
            title="Confirmed",
            start_at=FIXED_NOW + timedelta(days=1, hours=6),
            end_at=FIXED_NOW + timedelta(days=1, hours=7),
            price_inr=0,
        )
        db.session.add_all(
            [
                mumbai_guide,
                delhi_guide,
                traveler,
                visible_late,
                visible_early,
                other_city,
                past,
                inactive,
                confirmed,
                Booking(
                    slot=confirmed, traveler=traveler, status=BookingStatus.CONFIRMED
                ),
            ]
        )
        db.session.commit()

        all_titles = [slot.title for slot in list_public_slots()]
        city_titles = [slot.title for slot in list_public_slots(city="mUmBaI")]
        date_titles = [slot.title for slot in list_public_slots(slot_date="2030-01-02")]
        combined_titles = [
            slot.title
            for slot in list_public_slots(city="Mumbai", slot_date="2030-01-02")
        ]

        assert all_titles == ["Early Mumbai", "Delhi Walk", "Late Mumbai"]
        assert city_titles == ["Early Mumbai", "Late Mumbai"]
        assert date_titles == ["Early Mumbai", "Delhi Walk", "Late Mumbai"]
        assert combined_titles == ["Early Mumbai", "Late Mumbai"]
