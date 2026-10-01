from __future__ import annotations

from flask_wtf.csrf import generate_csrf

from app.extensions import db
from app.models import User, UserRole


def _register(client, *, email="traveler@example.com", role="traveler", city=""):
    return client.post(
        "/register",
        data={
            "name": "Test User",
            "email": email,
            "password": "correct-horse",
            "role": role,
            "city": city,
            "bio": "A short bio",
        },
        follow_redirects=True,
    )


def test_registers_traveler_and_hashes_password(client, app) -> None:
    response = _register(client)

    assert response.status_code == 200
    assert b"Registration successful." in response.data
    with app.app_context():
        user = db.session.scalar(
            db.select(User).where(User.email == "traveler@example.com")
        )
        assert user is not None
        assert user.role is UserRole.TRAVELER
        assert user.password_hash != "correct-horse"


def test_register_normalizes_email_and_rejects_case_insensitive_duplicate(
    client, app
) -> None:
    _register(client, email="Person@Example.com")
    client.post("/logout", follow_redirects=True)

    response = _register(client, email="person@example.COM")

    assert response.status_code == 200
    assert b"already exists" in response.data
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(User.id))) == 1


def test_registration_rejects_short_password(client) -> None:
    response = client.post(
        "/register",
        data={
            "name": "Short Password",
            "email": "short@example.com",
            "password": "short",
            "role": "traveler",
            "city": "",
            "bio": "",
        },
    )

    assert response.status_code == 200
    assert b"between 8 and 128 characters" in response.data


def test_guide_registration_requires_city(client) -> None:
    response = _register(client, email="guide@example.com", role="guide")

    assert response.status_code == 200
    assert b"City is required for guides." in response.data


def test_login_uses_one_generic_error_for_unknown_email_and_bad_password(
    client,
) -> None:
    _register(client)
    client.post("/logout", follow_redirects=True)

    unknown_email = client.post(
        "/login",
        data={"email": "unknown@example.com", "password": "wrong-password"},
    )
    bad_password = client.post(
        "/login",
        data={"email": "traveler@example.com", "password": "wrong-password"},
    )

    assert b"Invalid email or password." in unknown_email.data
    assert b"Invalid email or password." in bad_password.data
    assert unknown_email.data.count(b"Invalid email or password.") == 1
    assert bad_password.data.count(b"Invalid email or password.") == 1


def test_navigation_changes_for_traveler_and_guide(client) -> None:
    traveler = _register(client)
    assert b'data-testid="nav-user"' in traveler.data
    assert b'data-testid="nav-bookings"' in traveler.data
    assert b'data-testid="nav-guide-slots"' not in traveler.data
    assert b'data-testid="nav-login"' not in traveler.data
    assert b'data-testid="nav-register"' not in traveler.data
    client.post("/logout", follow_redirects=True)

    guide = _register(client, email="guide@example.com", role="guide", city="Mumbai")
    assert b'data-testid="nav-guide-slots"' in guide.data
    assert b'data-testid="nav-logout"' in guide.data


def test_logout_requires_csrf_token(client, app) -> None:
    _register(client)
    app.config["WTF_CSRF_ENABLED"] = True

    rejected = client.post("/logout")
    with client:
        client.get("/login")
        token = generate_csrf()

    accepted = client.post(
        "/logout",
        data={"csrf_token": token},
        follow_redirects=True,
    )

    assert rejected.status_code == 400
    assert accepted.status_code == 200
    assert b'data-testid="nav-login"' in accepted.data
