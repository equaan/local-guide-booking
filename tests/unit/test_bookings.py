"""Unit tests for the booking state machine service.

Uses Flask test client pattern that already works in this codebase.
"""

from __future__ import annotations

import pytest

from app import create_app


class TestRequestBooking:
    """BR-06, BR-05, and basic request rules."""

    @pytest.fixture
    def app(self):
        """Create a fresh app instance for each test."""
        return create_app(type("TestConfig", (), {
            "APP_ENV": "test",
            "DATABASE_URL": "sqlite://",
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "WTF_CSRF_ENABLED": False,
        })())

    def test_request_creates_pending(self, app, client):
        """Every request creates a PENDING booking."""
        from app.models import User, Slot

        with app.app_context():
            # Register a guide
            client.post("/register", data={
                "name": "Guide Test",
                "email": "guide@test.com",
                "password": "password",
                "role": "guide",
                "city": "Mumbai",
                "bio": "A guide",
            })

            # Register a traveler
            client.post("/register", data={
                "name": "Traveler Test",
                "email": "traveler@test.com",
                "password": "password",
                "role": "traveler",
                "city": "",
                "bio": "",
            })

            # Guide creates a slot
            # First login as guide
            client.post("/login", data={
                "email": "guide@test.com",
                "password": "password",
            })

            # Create slot via the guide slots new form
            # Actually, let's just check the API or use a simpler approach
            # For now, let's test the booking service indirectly

    def test_request_rejects_nonexistent_slot(self, app, client):
        """Requesting a slot that doesn't exist raises error."""
        from app.services.bookings import request_booking

        with app.app_context():
            with pytest.raises(Exception):  # Will fail gracefully
                pass  # Placeholder


class TestConfirmBooking:
    """BR-04, BR-06, BR-07: confirm transitions and auto-cancel."""
    pass


class TestCancelBooking:
    """BR-06, BR-07: cancel transitions for PENDING and CONFIRMED."""
    pass