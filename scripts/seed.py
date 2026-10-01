"""Create deterministic demo users and future availability slots."""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Slot, User, UserRole
from app.timeutils import now_ist

DEMO_USERS = (
    {
        "name": "Asha Sharma",
        "email": "asha@example.com",
        "role": UserRole.GUIDE,
        "city": "Mumbai",
        "bio": "Food and heritage walks in Mumbai.",
    },
    {
        "name": "Rohan Mehta",
        "email": "rohan@example.com",
        "role": UserRole.GUIDE,
        "city": "Delhi",
        "bio": "History and architecture tours in Delhi.",
    },
    {
        "name": "Priya Nair",
        "email": "priya@example.com",
        "role": UserRole.TRAVELER,
        "city": None,
        "bio": None,
    },
    {
        "name": "Kabir Singh",
        "email": "kabir@example.com",
        "role": UserRole.TRAVELER,
        "city": None,
        "bio": None,
    },
)

DEMO_SLOTS = (
    ("asha@example.com", "Mumbai market walk", 1, 10, 1500),
    ("asha@example.com", "Mumbai heritage walk", 2, 14, 1800),
    ("asha@example.com", "Mumbai street food tour", 3, 17, 1600),
    ("rohan@example.com", "Delhi old city walk", 1, 9, 1400),
    ("rohan@example.com", "Delhi monuments tour", 2, 13, 2000),
    ("rohan@example.com", "Delhi evening walk", 3, 18, 1700),
)


def seed_demo_data() -> None:
    """Use stable email and title keys so reruns preserve the same demo rows."""
    for user_data in DEMO_USERS:
        existing_user = db.session.scalar(
            db.select(User).where(User.email == user_data["email"])
        )
        if existing_user is None:
            db.session.add(
                User(
                    **user_data,
                    password_hash=generate_password_hash("demo-only-account"),
                )
            )

    db.session.flush()
    start_of_tomorrow = now_ist().replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)

    for email, title, day_offset, hour, price_inr in DEMO_SLOTS:
        guide = db.session.scalar(db.select(User).where(User.email == email))
        existing_slot = db.session.scalar(
            db.select(Slot).where(Slot.guide_id == guide.id, Slot.title == title)
        )
        if existing_slot is None:
            start_at = start_of_tomorrow + timedelta(days=day_offset - 1, hours=hour)
            db.session.add(
                Slot(
                    guide_id=guide.id,
                    title=title,
                    start_at=start_at,
                    end_at=start_at + timedelta(hours=2),
                    price_inr=price_inr,
                )
            )

    db.session.commit()


def main() -> None:
    app = create_app()
    with app.app_context():
        seed_demo_data()


if __name__ == "__main__":
    main()
