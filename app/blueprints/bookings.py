"""Thin request, confirmation, and cancellation routes for booking actions."""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app import timeutils
from app.extensions import db
from app.forms import BookingRequestForm, CancelBookingForm
from app.models import Booking, BookingEvent, BookingStatus, Slot, UserRole
from app.services.bookings import (
    BookingValidationError,
    cancel_booking,
    confirm_booking,
    request_booking,
)

bookings_bp = Blueprint("bookings", __name__)


def _booking_or_404(booking_id: int) -> Booking:
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        abort(404)
    return booking


def _cancel_redirect(booking: Booking) -> str:
    if current_user.role is UserRole.GUIDE:
        return url_for("guide.slots")
    return url_for("slots.slot_detail", slot_id=booking.slot_id)


@bookings_bp.get("/bookings")
@login_required
def bookings_list():
    """Show only bookings in which the current user participates."""
    if current_user.role is UserRole.TRAVELER:
        statement = select(Booking).where(Booking.traveler_id == current_user.id)
    else:
        statement = select(Booking).join(Slot).where(Slot.guide_id == current_user.id)
    bookings = db.session.scalars(statement.order_by(Booking.created_at.desc())).all()
    return render_template("bookings/list.html", bookings=bookings)


@bookings_bp.get("/bookings/<int:booking_id>")
@login_required
def booking_detail(booking_id: int):
    """Show a booking only to its traveler or the guide who owns its slot."""
    booking = _booking_or_404(booking_id)
    is_guide = booking.slot.guide_id == current_user.id
    is_traveler = booking.traveler_id == current_user.id
    if not (is_guide or is_traveler):
        abort(404)

    events = db.session.scalars(
        select(BookingEvent)
        .where(BookingEvent.booking_id == booking.id)
        .order_by(BookingEvent.created_at.asc())
    ).all()
    action_allowed = booking.slot.start_at > timeutils.now_ist()
    can_confirm = (
        action_allowed and is_guide and booking.status is BookingStatus.PENDING
    )
    can_cancel = action_allowed and booking.status in (
        BookingStatus.PENDING,
        BookingStatus.CONFIRMED,
    )
    return render_template(
        "bookings/detail.html",
        booking=booking,
        can_cancel=can_cancel,
        can_confirm=can_confirm,
        cancel_form=CancelBookingForm(),
        events=events,
    )


@bookings_bp.post("/slots/<int:slot_id>/book")
@login_required
def request_booking_action(slot_id: int):
    if current_user.role is not UserRole.TRAVELER:
        abort(403)
    form = BookingRequestForm()
    if not form.validate_on_submit():
        flash("Please correct the booking request.", "error")
        return redirect(url_for("slots.slot_detail", slot_id=slot_id))
    try:
        request_booking(slot_id, current_user.id, form.note.data)
    except BookingValidationError as error:
        flash(str(error), "error")
    else:
        flash("Booking requested.", "success")
    return redirect(url_for("slots.slot_detail", slot_id=slot_id))


@bookings_bp.post("/bookings/<int:booking_id>/confirm")
@login_required
def confirm_booking_action(booking_id: int):
    if current_user.role is not UserRole.GUIDE:
        abort(403)
    booking = _booking_or_404(booking_id)
    if booking.slot.guide_id != current_user.id:
        abort(404)
    try:
        confirm_booking(booking.id, current_user.id)
    except BookingValidationError as error:
        flash(str(error), "error")
    else:
        flash("Booking confirmed.", "success")
    return redirect(request.referrer or url_for("guide.slots"))


@bookings_bp.post("/bookings/<int:booking_id>/cancel")
@login_required
def cancel_booking_action(booking_id: int):
    booking = _booking_or_404(booking_id)
    if (
        booking.traveler_id != current_user.id
        and booking.slot.guide_id != current_user.id
    ):
        abort(404)
    form = CancelBookingForm()
    if not form.validate_on_submit():
        flash("Please correct the cancellation reason.", "error")
        return redirect(request.referrer or _cancel_redirect(booking))
    try:
        cancel_booking(booking.id, current_user.id, form.reason.data)
    except BookingValidationError as error:
        flash(str(error), "error")
    else:
        flash("Booking cancelled.", "success")
    return redirect(request.referrer or _cancel_redirect(booking))
