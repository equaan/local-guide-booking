from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.extensions import db
from app.models import Slot

NOW = datetime(2030, 1, 1, 9, 0)


def _register(client, *, email: str, role: str, city: str = ""):
    return client.post(
        "/register",
        data={
            "name": role.title(),
            "email": email,
            "password": "correct-horse",
            "role": role,
            "city": city,
            "bio": "",
        },
    )


def _slot_form(start: datetime, end: datetime) -> dict[str, str]:
    return {
        "title": "Metrics walk",
        "start_at": start.isoformat(timespec="minutes"),
        "end_at": end.isoformat(timespec="minutes"),
        "price_inr": "500",
    }


def test_metrics_exposes_required_instruments_after_routes(
    client, app, monkeypatch
) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: NOW)
    client.get("/health")
    _register(client, email="guide@example.com", role="guide", city="Mumbai")
    client.post(
        "/guide/slots/new",
        data=_slot_form(NOW + timedelta(hours=1), NOW + timedelta(hours=2)),
    )
    with app.app_context():
        slot_id = db.session.scalar(db.select(Slot.id))

    client.get(f"/slots/{slot_id}")
    client.post("/logout")
    _register(client, email="traveler@example.com", role="traveler")
    client.post(f"/slots/{slot_id}/book", data={"note": "Metrics test"})

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    assert b"lgb_http_requests_total" in response.data
    assert b"lgb_http_request_duration_seconds" in response.data
    assert b"lgb_bookings_transitions_total" in response.data
    assert b"lgb_users_registered_total" in response.data
    assert b"lgb_slots_created_total" in response.data
    assert b"lgb_bookings_current" in response.data
    assert b'lgb_users_registered_total{role="guide"}' in response.data
    assert b'lgb_users_registered_total{role="traveler"}' in response.data
    assert b'from_status="NONE",to_status="PENDING"' in response.data
    assert b'lgb_bookings_current{status="PENDING"}' in response.data
    assert b'endpoint="/slots/<int:slot_id>"' in response.data
    assert f'endpoint="/slots/{slot_id}"'.encode() not in response.data


def test_login_request_logging_omits_password(client, caplog) -> None:
    password = "do-not-log-this-password"
    caplog.set_level(logging.INFO, logger="app")
    caplog.clear()

    response = client.post(
        "/login",
        data={"email": "unknown@example.com", "password": password},
    )

    assert response.status_code == 200
    assert password not in caplog.text
    assert "request method=POST path=/login status=200" in caplog.text
