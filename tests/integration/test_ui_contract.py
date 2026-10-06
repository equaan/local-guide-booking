from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models import Booking, BookingEvent, BookingStatus, Slot, User, UserRole

NOW = datetime(2030, 1, 1, 9, 0)


def _login(client, user_id: int) -> None:
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _page_data() -> dict[str, int]:
    guide = User(
        name="Guide",
        email="guide@example.com",
        password_hash="hash",
        role=UserRole.GUIDE,
        city="Mumbai",
    )
    traveler = User(
        name="Traveler",
        email="traveler@example.com",
        password_hash="hash",
        role=UserRole.TRAVELER,
    )
    slot = Slot(
        guide=guide,
        title="Harbor walk",
        start_at=NOW + timedelta(hours=1),
        end_at=NOW + timedelta(hours=2),
    )
    db.session.add_all([guide, traveler, slot])
    db.session.flush()
    booking = Booking(
        slot=slot,
        traveler=traveler,
        status=BookingStatus.PENDING,
    )
    db.session.add(booking)
    db.session.flush()
    db.session.add(
        BookingEvent(
            booking=booking,
            from_status=None,
            to_status=BookingStatus.PENDING,
            actor=traveler,
        )
    )
    db.session.commit()
    return {
        "guide": guide.id,
        "traveler": traveler.id,
        "slot": slot.id,
        "booking": booking.id,
    }


def _assert_title_and_css(response) -> None:
    assert b"<title>" in response.data
    assert b"/static/app.css" in response.data


def test_pages_keep_the_important_selector_and_label_contract(
    client, app, monkeypatch
) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    with app.app_context():
        data = _page_data()

    home = client.get("/")
    assert b'data-testid="nav-slots"' in home.data
    assert b'data-testid="nav-login"' in home.data
    assert b'data-testid="nav-register"' in home.data
    _assert_title_and_css(home)

    register = client.get("/register")
    for field_id in ("name", "email", "password", "role", "city", "bio"):
        assert f'id="{field_id}"'.encode() in register.data
        assert f'for="{field_id}"'.encode() in register.data
    assert b'id="submit-register"' in register.data
    _assert_title_and_css(register)

    login = client.get("/login")
    for field_id in ("email", "password"):
        assert f'id="{field_id}"'.encode() in login.data
        assert f'for="{field_id}"'.encode() in login.data
    assert b'id="submit-login"' in login.data
    _assert_title_and_css(login)

    slots = client.get("/slots")
    assert b'id="filter-city"' in slots.data
    assert b'id="filter-date"' in slots.data
    assert b'id="apply-filter"' in slots.data
    assert b'data-testid="slot-row"' in slots.data
    assert b'data-testid="slot-link"' in slots.data
    _assert_title_and_css(slots)

    _login(client, data["traveler"])
    detail = client.get(f"/slots/{data['slot']}")
    assert b'id="note"' in detail.data
    assert b'id="book-btn"' in detail.data
    assert b'for="note"' in detail.data
    _assert_title_and_css(detail)

    bookings = client.get("/bookings")
    assert b'data-testid="nav-bookings"' in bookings.data
    assert b'data-testid="booking-row"' in bookings.data
    assert b'data-testid="booking-status">PENDING' in bookings.data

    booking_detail = client.get(f"/bookings/{data['booking']}")
    assert b'data-testid="timeline-item"' in booking_detail.data
    assert b'id="cancel-btn"' in booking_detail.data
    assert b'id="reason"' in booking_detail.data
    assert b'for="reason"' in booking_detail.data

    _login(client, data["guide"])
    guide_slots = client.get("/guide/slots")
    assert b'data-testid="nav-guide-slots"' in guide_slots.data
    assert b'data-testid="guide-slot-row"' in guide_slots.data
    assert b'data-testid="slot-status"' in guide_slots.data

    new_slot = client.get("/guide/slots/new")
    for field_id in ("title", "start_at", "end_at", "price_inr"):
        assert f'id="{field_id}"'.encode() in new_slot.data
        assert f'for="{field_id}"'.encode() in new_slot.data
    assert b'id="submit-slot"' in new_slot.data

    _login(client, data["traveler"])
    forbidden = client.get("/guide/slots")
    assert forbidden.status_code == 403
    assert b"This area is not available to you." in forbidden.data


def test_custom_error_pages_do_not_expose_exception_details(client, app) -> None:
    def raise_private_error():
        raise RuntimeError("private diagnostic")

    app.add_url_rule("/test-error", "test_error", raise_private_error)
    app.config["PROPAGATE_EXCEPTIONS"] = False

    not_found = client.get("/missing-page")
    assert not_found.status_code == 404
    assert b"That page is not here." in not_found.data
    assert b"Traceback" not in not_found.data

    server_error = client.get("/test-error")

    assert server_error.status_code == 500
    assert b"We could not complete that request." in server_error.data
    assert b"private diagnostic" not in server_error.data
    assert b"Traceback" not in server_error.data
