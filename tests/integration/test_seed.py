from __future__ import annotations

from sqlalchemy import func, select

from app.extensions import db
from app.models import Booking, BookingEvent, Slot, User
from scripts.seed import seed_demo_data


def _row_counts() -> tuple[int, int, int, int]:
    return (
        db.session.scalar(select(func.count()).select_from(User)),
        db.session.scalar(select(func.count()).select_from(Slot)),
        db.session.scalar(select(func.count()).select_from(Booking)),
        db.session.scalar(select(func.count()).select_from(BookingEvent)),
    )


def test_seed_is_idempotent(app) -> None:
    with app.app_context():
        seed_demo_data()
        first_counts = _row_counts()

        seed_demo_data()

        assert first_counts == (4, 6, 0, 0)
        assert _row_counts() == first_counts
