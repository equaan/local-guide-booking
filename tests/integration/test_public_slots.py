from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models import Booking, BookingStatus, Slot, User, UserRole

FIXED_NOW = datetime(2030, 1, 1, 9, 0)


def _public_data(app) -> tuple[int, int]:
    with app.app_context():
        guide = User(
            name="Asha Guide",
            email="public-guide@example.com",
            password_hash="hash",
            role=UserRole.GUIDE,
            city="Mumbai",
            bio="Heritage walks.",
        )
        traveler = User(
            name="Public Traveler",
            email="public-booker@example.com",
            password_hash="hash",
            role=UserRole.TRAVELER,
        )
        visible = Slot(
            guide=guide,
            title="Public heritage walk",
            start_at=FIXED_NOW + timedelta(days=1, hours=1),
            end_at=FIXED_NOW + timedelta(days=1, hours=2),
            price_inr=900,
        )
        confirmed = Slot(
            guide=guide,
            title="Unavailable walk",
            start_at=FIXED_NOW + timedelta(days=1, hours=3),
            end_at=FIXED_NOW + timedelta(days=1, hours=4),
            price_inr=1000,
        )
        db.session.add_all([guide, traveler, visible, confirmed])
        db.session.flush()
        db.session.add(
            Booking(slot=confirmed, traveler=traveler, status=BookingStatus.CONFIRMED)
        )
        db.session.commit()
        return visible.id, confirmed.id


def test_public_list_filters_and_empty_state(client, app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    visible_id, confirmed_id = _public_data(app)

    response = client.get("/slots?city=MUMBAI&date=2030-01-02")
    empty = client.get("/slots?city=Delhi")

    assert response.status_code == 200
    assert f'data-slot-id="{visible_id}"'.encode() in response.data
    assert f'data-slot-id="{confirmed_id}"'.encode() not in response.data
    assert b"Public heritage walk" in response.data
    assert b'data-testid="empty-state"' in empty.data


def test_public_detail_shows_guide_and_availability(client, app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    visible_id, _ = _public_data(app)

    response = client.get(f"/slots/{visible_id}")

    assert response.status_code == 200
    assert b"Asha Guide" in response.data
    assert b"Mumbai" in response.data
    assert b"Heritage walks." in response.data
    assert b"INR 900" in response.data
    assert b"Available" in response.data


def test_slots_api_matches_public_filters(client, app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    visible_id, _ = _public_data(app)

    response = client.get("/api/v1/slots?city=mumbai&date=2030-01-02")

    assert response.status_code == 200
    assert response.get_json() == {
        "slots": [
            {
                "city": "Mumbai",
                "end_at": "2030-01-02T11:00:00",
                "guide": "Asha Guide",
                "id": visible_id,
                "price_inr": 900,
                "start_at": "2030-01-02T10:00:00",
                "title": "Public heritage walk",
            }
        ]
    }


def test_missing_slot_detail_returns_404(client) -> None:
    assert client.get("/slots/999").status_code == 404
