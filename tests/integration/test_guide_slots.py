from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models import Slot, User

FIXED_NOW = datetime(2030, 1, 1, 9, 0)


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
        follow_redirects=True,
    )


def _slot_form(start: datetime, end: datetime, **overrides):
    data = {
        "title": "Mumbai heritage walk",
        "start_at": start.isoformat(timespec="minutes"),
        "end_at": end.isoformat(timespec="minutes"),
        "price_inr": "750",
    }
    data.update(overrides)
    return data


def test_traveler_gets_403_on_guide_pages(client) -> None:
    _register(client, email="traveler@example.com", role="traveler")

    assert client.get("/guide/slots").status_code == 403
    assert client.get("/guide/slots/new").status_code == 403


def test_guide_can_create_list_and_deactivate_own_slot(
    client, app, monkeypatch
) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    _register(client, email="guide@example.com", role="guide", city="Mumbai")

    response = client.post(
        "/guide/slots/new",
        data=_slot_form(FIXED_NOW + timedelta(hours=1), FIXED_NOW + timedelta(hours=2)),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Mumbai heritage walk" in response.data
    assert b"available" in response.data
    with app.app_context():
        slot = db.session.scalar(db.select(Slot))
        guide = db.session.scalar(
            db.select(User).where(User.email == "guide@example.com")
        )
        assert slot is not None
        assert slot.guide_id == guide.id
        slot_id = slot.id

    response = client.post(f"/guide/slots/{slot_id}/deactivate", follow_redirects=True)

    assert b"Slot deactivated." in response.data
    assert b"inactive" in response.data


def test_slot_creation_rejects_past_duration_and_overlap(client, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    _register(client, email="guide@example.com", role="guide", city="Mumbai")
    client.post(
        "/guide/slots/new",
        data=_slot_form(FIXED_NOW + timedelta(hours=1), FIXED_NOW + timedelta(hours=3)),
    )

    past = client.post(
        "/guide/slots/new",
        data=_slot_form(FIXED_NOW - timedelta(hours=2), FIXED_NOW - timedelta(hours=1)),
    )
    short = client.post(
        "/guide/slots/new",
        data=_slot_form(
            FIXED_NOW + timedelta(hours=4),
            FIXED_NOW + timedelta(hours=4, minutes=15),
        ),
    )
    overlap = client.post(
        "/guide/slots/new",
        data=_slot_form(FIXED_NOW + timedelta(hours=2), FIXED_NOW + timedelta(hours=4)),
    )

    assert b"future" in past.data
    assert b"30 minutes" in short.data
    assert b"overlaps" in overlap.data


def test_guide_cannot_deactivate_another_guides_slot(client, app, monkeypatch) -> None:
    monkeypatch.setattr("app.timeutils.now_ist", lambda: FIXED_NOW)
    _register(client, email="first@example.com", role="guide", city="Mumbai")
    client.post(
        "/guide/slots/new",
        data=_slot_form(FIXED_NOW + timedelta(hours=1), FIXED_NOW + timedelta(hours=2)),
    )
    with app.app_context():
        slot_id = db.session.scalar(db.select(Slot)).id
    client.post("/logout", follow_redirects=True)
    _register(client, email="second@example.com", role="guide", city="Delhi")

    assert client.post(f"/guide/slots/{slot_id}/deactivate").status_code == 404
