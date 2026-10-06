from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models import Booking, BookingStatus, Slot, User, UserRole

NOW = datetime(2030, 1, 1, 9, 0)


def _user(name: str, email: str, role: UserRole, city: str | None = None) -> User:
    return User(
        name=name,
        email=email,
        password_hash="hash",
        role=role,
        city=city,
    )


def _data() -> tuple[int, int, int, int]:
    guide = _user("Guide", "guide@example.com", UserRole.GUIDE, "Mumbai")
    traveler = _user("Traveler", "traveler@example.com", UserRole.TRAVELER)
    other = _user("Other", "other@example.com", UserRole.TRAVELER)
    slot = Slot(
        guide=guide,
        title="Walking tour",
        start_at=NOW + timedelta(hours=1),
        end_at=NOW + timedelta(hours=3),
    )
    db.session.add_all([guide, traveler, other, slot])
    db.session.commit()
    return slot.id, guide.id, traveler.id, other.id


def _login(client, user_id: int) -> None:
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_traveler_can_request_then_guide_can_confirm_and_cancel(
    client, app, monkeypatch
) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        slot_id, guide_id, traveler_id, _ = _data()
    _login(client, traveler_id)

    requested = client.post(
        f"/slots/{slot_id}/book",
        data={"note": "Looking forward to it."},
        follow_redirects=True,
    )
    assert requested.status_code == 200
    assert b"Booking requested." in requested.data
    with app.app_context():
        booking = db.session.scalar(db.select(Booking))
        booking_id = booking.id
        assert booking.status is BookingStatus.PENDING

    _login(client, guide_id)
    confirmed = client.post(f"/bookings/{booking_id}/confirm", follow_redirects=True)
    assert confirmed.status_code == 200
    assert b"Booking confirmed." in confirmed.data
    with app.app_context():
        assert db.session.get(Booking, booking_id).status is BookingStatus.CONFIRMED

    _login(client, traveler_id)
    cancelled = client.post(
        f"/bookings/{booking_id}/cancel",
        data={"reason": "Schedule changed"},
        follow_redirects=True,
    )
    assert cancelled.status_code == 200
    assert b"Booking cancelled." in cancelled.data
    with app.app_context():
        assert db.session.get(Booking, booking_id).status is BookingStatus.CANCELLED


def test_booking_routes_enforce_role_and_ownership(client, app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        slot_id, guide_id, traveler_id, other_id = _data()
        booking = Booking(
            slot_id=slot_id,
            traveler_id=traveler_id,
            status=BookingStatus.PENDING,
        )
        db.session.add(booking)
        db.session.commit()
        booking_id = booking.id

    _login(client, guide_id)
    assert client.post(f"/slots/{slot_id}/book", data={"note": "x"}).status_code == 403

    _login(client, traveler_id)
    assert client.post(f"/bookings/{booking_id}/confirm").status_code == 403

    _login(client, other_id)
    assert (
        client.post(f"/bookings/{booking_id}/cancel", data={"reason": "x"}).status_code
        == 404
    )


def test_booking_actions_reject_started_slot(client, app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        slot_id, guide_id, traveler_id, _ = _data()
        slot = db.session.get(Slot, slot_id)
        slot.start_at = NOW - timedelta(minutes=1)
        booking = Booking(
            slot_id=slot_id,
            traveler_id=traveler_id,
            status=BookingStatus.PENDING,
        )
        db.session.add(booking)
        db.session.commit()
        booking_id = booking.id

    _login(client, guide_id)
    response = client.post(f"/bookings/{booking_id}/confirm", follow_redirects=True)

    assert b"after the slot has started" in response.data


def test_booking_actions_validate_input_and_hide_missing_bookings(
    client, app, monkeypatch
) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        slot_id, guide_id, traveler_id, _ = _data()

    _login(client, traveler_id)
    invalid_request = client.post(
        f"/slots/{slot_id}/book",
        data={"note": "x" * 301},
        follow_redirects=True,
    )
    assert b"Please correct the booking request." in invalid_request.data
    assert client.post("/bookings/999/cancel", data={"reason": "x"}).status_code == 404

    _login(client, guide_id)
    assert client.post("/bookings/999/confirm").status_code == 404


def test_traveler_cannot_cancel_after_slot_starts(client, app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        slot_id, _, traveler_id, _ = _data()
        slot = db.session.get(Slot, slot_id)
        slot.start_at = NOW - timedelta(minutes=1)
        booking = Booking(
            slot_id=slot_id,
            traveler_id=traveler_id,
            status=BookingStatus.PENDING,
        )
        db.session.add(booking)
        db.session.commit()
        booking_id = booking.id

    _login(client, traveler_id)
    response = client.post(
        f"/bookings/{booking_id}/cancel",
        data={"reason": "Too late"},
        follow_redirects=True,
    )

    assert b"after the slot has started" in response.data
    with app.app_context():
        assert db.session.get(Booking, booking_id).status is BookingStatus.PENDING
