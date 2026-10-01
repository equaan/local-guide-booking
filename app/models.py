"""Database models for users, availability slots, and booking history."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from flask_login import UserMixin
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.timeutils import now_ist


class UserRole(StrEnum):
    """Roles supported by the MVP."""

    TRAVELER = "traveler"
    GUIDE = "guide"


class BookingStatus(StrEnum):
    """Persisted booking states used by the booking state machine."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, native_enum=False, create_constraint=True), nullable=False
    )
    city: Mapped[str | None] = mapped_column(String(80))
    bio: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_ist, nullable=False
    )

    slots: Mapped[list[Slot]] = relationship(back_populates="guide")
    bookings: Mapped[list[Booking]] = relationship(back_populates="traveler")
    acted_booking_events: Mapped[list[BookingEvent]] = relationship(
        back_populates="actor", foreign_keys="BookingEvent.actor_id"
    )


class Slot(db.Model):
    __tablename__ = "slots"
    __table_args__ = (Index("ix_slots_guide_id_start_at", "guide_id", "start_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    price_inr: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_ist, nullable=False
    )

    guide: Mapped[User] = relationship(back_populates="slots")
    bookings: Mapped[list[Booking]] = relationship(back_populates="slot")


class Booking(db.Model):
    __tablename__ = "bookings"
    __table_args__ = (
        Index(
            "uq_bookings_confirmed_slot",
            "slot_id",
            unique=True,
            sqlite_where=text("status = 'CONFIRMED'"),
            postgresql_where=text("status = 'CONFIRMED'"),
        ),
        Index(
            "uq_bookings_active_slot_traveler",
            "slot_id",
            "traveler_id",
            unique=True,
            sqlite_where=text("status IN ('PENDING', 'CONFIRMED')"),
            postgresql_where=text("status IN ('PENDING', 'CONFIRMED')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"), nullable=False)
    traveler_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        SqlEnum(BookingStatus, native_enum=False, create_constraint=True),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_ist, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_ist, onupdate=now_ist, nullable=False
    )

    slot: Mapped[Slot] = relationship(back_populates="bookings")
    traveler: Mapped[User] = relationship(back_populates="bookings")
    events: Mapped[list[BookingEvent]] = relationship(back_populates="booking")


class BookingEvent(db.Model):
    __tablename__ = "booking_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    from_status: Mapped[BookingStatus | None] = mapped_column(
        SqlEnum(BookingStatus, native_enum=False, create_constraint=True)
    )
    to_status: Mapped[BookingStatus] = mapped_column(
        SqlEnum(BookingStatus, native_enum=False, create_constraint=True),
        nullable=False,
    )
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_ist, nullable=False
    )

    booking: Mapped[Booking] = relationship(back_populates="events")
    actor: Mapped[User | None] = relationship(
        back_populates="acted_booking_events", foreign_keys=[actor_id]
    )
