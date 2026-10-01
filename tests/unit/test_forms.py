from __future__ import annotations

from app.forms import RegistrationForm


def test_registration_form_requires_eight_character_password(app) -> None:
    with app.test_request_context():
        form = RegistrationForm(
            data={
                "name": "Traveler",
                "email": "traveler@example.com",
                "password": "short",
                "role": "traveler",
                "city": "",
                "bio": "",
            }
        )

        assert form.validate() is False
        assert any("between 8 and 128" in error for error in form.password.errors)


def test_registration_form_requires_city_for_guides(app) -> None:
    with app.test_request_context():
        form = RegistrationForm(
            data={
                "name": "Guide",
                "email": "guide@example.com",
                "password": "correct-horse",
                "role": "guide",
                "city": "",
                "bio": "",
            }
        )

        assert form.validate() is False
        assert "City is required for guides." in form.city.errors
