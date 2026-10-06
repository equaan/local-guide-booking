from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models import Booking, BookingEvent, BookingStatus, Slot, User, UserRole

NOW = datetime(2030, 1, 1, 9, 0)


def _user(name: str, email: str, role: UserRole, city: str | None = None) -> User:
    return User(
        name=name,
        email=email,
        password_hash="hash",
        role=role,
        city=city,
    )


def _login(client, user_id: int) -> None:
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _booking_page_data() -> dict[str, int]:
    guide = _user("Guide", "guide@example.com", UserRole.GUIDE, "Mumbai")
    other_guide = _user(
        "Other guide", "other-guide@example.com", UserRole.GUIDE, "Pune"
    )
    traveler = _user("Traveler", "traveler@example.com", UserRole.TRAVELER)
    other_traveler = _user("Other traveler", "other@example.com", UserRole.TRAVELER)
    empty_traveler = _user("Empty", "empty@example.com", UserRole.TRAVELER)
    oldest_slot = Slot(
        guide=guide,
        title="Oldest tour",
        start_at=NOW + timedelta(hours=1),
        end_at=NOW + timedelta(hours=2),
    )
    newest_slot = Slot(
        guide=guide,
        title="Newest tour",
        start_at=NOW + timedelta(hours=3),
        end_at=NOW + timedelta(hours=4),
    )
    other_slot = Slot(
        guide=other_guide,
        title="Other guide tour",
        start_at=NOW + timedelta(hours=5),
        end_at=NOW + timedelta(hours=6),
    )
    db.session.add_all(
        [
            guide,
            other_guide,
            traveler,
            other_traveler,
            empty_traveler,
            oldest_slot,
            newest_slot,
            other_slot,
        ]
    )
    db.session.flush()
    oldest = Booking(
        slot=oldest_slot,
        traveler=traveler,
        status=BookingStatus.CANCELLED,
        created_at=NOW - timedelta(minutes=2),
    )
    newest = Booking(
        slot=newest_slot,
        traveler=traveler,
        status=BookingStatus.PENDING,
        created_at=NOW - timedelta(minutes=1),
    )
    foreign = Booking(
        slot=other_slot,
        traveler=other_traveler,
        status=BookingStatus.PENDING,
    )
    db.session.add_all([oldest, newest, foreign])
    db.session.commit()
    return {
        "guide": guide.id,
        "traveler": traveler.id,
        "other_traveler": other_traveler.id,
        "empty_traveler": empty_traveler.id,
        "oldest": oldest.id,
        "newest": newest.id,
        "foreign": foreign.id,
    }


def test_booking_list_is_role_scoped_and_newest_first(client, app) -> None:
    with app.app_context():
        data = _booking_page_data()

    _login(client, data["traveler"])
    traveler_response = client.get("/bookings")

    assert traveler_response.status_code == 200
    assert f'data-booking-id="{data["newest"]}"'.encode() in traveler_response.data
    assert f'data-booking-id="{data["oldest"]}"'.encode() in traveler_response.data
    assert f'data-booking-id="{data["foreign"]}"'.encode() not in traveler_response.data
    assert traveler_response.data.index(b"Newest tour") < traveler_response.data.index(
        b"Oldest tour"
    )
    assert b'data-testid="booking-status">PENDING' in traveler_response.data

    _login(client, data["guide"])
    guide_response = client.get("/bookings")

    assert guide_response.status_code == 200
    assert f'data-booking-id="{data["newest"]}"'.encode() in guide_response.data
    assert f'data-booking-id="{data["oldest"]}"'.encode() in guide_response.data
    assert f'data-booking-id="{data["foreign"]}"'.encode() not in guide_response.data


def test_booking_list_has_an_empty_state(client, app) -> None:
    with app.app_context():
        data = _booking_page_data()

    _login(client, data["empty_traveler"])
    response = client.get("/bookings")

    assert response.status_code == 200
    assert b'data-testid="empty-state"' in response.data


def test_booking_detail_has_timeline_and_role_specific_controls(
    client, app, monkeypatch
) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        data = _booking_page_data()
        booking = db.session.get(Booking, data["newest"])
        db.session.add(
            BookingEvent(
                booking_id=booking.id,
                from_status=None,
                to_status=BookingStatus.PENDING,
                actor_id=data["traveler"],
                created_at=NOW - timedelta(minutes=1),
            )
        )
        db.session.commit()

    _login(client, data["guide"])
    guide_response = client.get(f"/bookings/{data['newest']}")

    assert guide_response.status_code == 200
    assert b'id="confirm-btn"' in guide_response.data
    assert b'id="cancel-btn"' in guide_response.data
    assert b'id="reason"' in guide_response.data
    assert guide_response.data.count(b'data-testid="timeline-item"') == 1
    assert b"None to PENDING" in guide_response.data
    assert b"by Traveler" in guide_response.data

    _login(client, data["traveler"])
    traveler_response = client.get(f"/bookings/{data['newest']}")

    assert traveler_response.status_code == 200
    assert b'id="confirm-btn"' not in traveler_response.data
    assert b'id="cancel-btn"' in traveler_response.data


def test_booking_detail_hides_actions_after_slot_starts(
    client, app, monkeypatch
) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        data = _booking_page_data()
        booking = db.session.get(Booking, data["newest"])
        booking.slot.start_at = NOW
        db.session.commit()

    _login(client, data["guide"])
    response = client.get(f"/bookings/{data['newest']}")

    assert response.status_code == 200
    assert b'id="confirm-btn"' not in response.data
    assert b'id="cancel-btn"' not in response.data


def test_booking_detail_hides_foreign_bookings(client, app) -> None:
    with app.app_context():
        data = _booking_page_data()

    _login(client, data["other_traveler"])
    response = client.get(f"/bookings/{data['newest']}")

    assert response.status_code == 404
