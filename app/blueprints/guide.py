from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.forms import SlotForm
from app.models import BookingStatus, User, UserRole, Booking, Slot
from app.services.bookings import (
    BookingValidationError,
    cancel_booking,
    confirm_booking,
    request_booking,
)
from app.services.slots import (
    SlotValidationError,
    create_slot,
    deactivate_slot,
    list_guide_slots,
)

guide_bp = Blueprint("guide", __name__)


def _require_guide() -> None:
    if current_user.role is not UserRole.GUIDE:
        abort(403)


@guide_bp.get("/guide/slots")
@login_required
def slots():
    _require_guide()
    return render_template("guide/slots.html", slots=list_guide_slots(current_user.id))


@guide_bp.route("/guide/slots/new", methods=["GET", "POST"])
@login_required
def new_slot():
    _require_guide()
    form = SlotForm()
    if form.validate_on_submit():
        try:
            start_at = datetime.fromisoformat(form.start_at.data)
            end_at = datetime.fromisoformat(form.end_at.data)
            create_slot(
                current_user.id,
                form.title.data,
                start_at,
                end_at,
                form.price_inr.data,
            )
        except (SlotValidationError, ValueError) as error:
            form.start_at.errors.append(str(error))
        else:
            flash("Slot created successfully.", "success")
            return redirect(url_for("guide.slots"))
    return render_template("guide/new_slot.html", form=form)


@guide_bp.post("/guide/slots/<int:slot_id>/deactivate")
@login_required
def deactivate(slot_id: int):
    _require_guide()
    slot = db.session.get(Slot, slot_id)
    if slot is None:
        abort(404)
    if slot.guide_id != current_user.id:
        abort(404)
    try:
        deactivate_slot(slot)
    except SlotValidationError as error:
        flash(str(error), "error")
    else:
        flash("Slot deactivated.", "success")
    return redirect(url_for("guide.slots"))


# ----------------------------------------------------------------------------
# BR-13: My bookings list
# ----------------------------------------------------------------------------


@guide_bp.get("/bookings")
@login_required
def bookings_list():
    """Show bookings for the logged-in user.

    - Traveler sees their own bookings, newest first.
    - Guide sees bookings on their own slots, newest first.
    """
    user = current_user

    if user.role is UserRole.TRAVELER:
        bookings = (
            select(Booking)
            .where(Booking.traveler_id == user.id)
            .order_by(Booking.created_at.desc())
        )
    else:  # GUIDE
        bookings = (
            select(Booking)
            .join(Slot, Booking.slot_id == Slot.id)
            .where(Slot.guide_id == user.id)
            .order_by(Booking.created_at.desc())
        )

    bookings = db.session.scalars(bookings).all()

    return render_template(
        "guide/bookings_list.html",
        bookings=bookings,
        is_guide=user.role is UserRole.GUIDE,
    )


# ----------------------------------------------------------------------------
# BR-14: Booking detail page
# ----------------------------------------------------------------------------


@guide_bp.get("/bookings/<int:booking_id>")
@login_required
def booking_detail(booking_id: int):
    """Show booking detail with status timeline.

    - Traveler owner or slot's guide can view.
    - Shows confirm/cancel buttons where allowed.
    - Shows status timeline with from_status, to_status, actor, and time.
    """
    booking = db.session.scalar(
        select(Booking).where(Booking.id == booking_id)
    )
    if booking is None:
        abort(404)

    # Ownership check (BR-07)
    is_traveler = booking.traveler_id == current_user.id
    is_guide = False
    slot = db.session.scalar(select(Slot).where(Slot.id == booking.slot_id))
    if slot is not None and slot.guide_id == current_user.id:
        is_guide = True

    if not is_traveler and not is_guide:
        abort(403)

    # Determine allowed actions
    can_confirm = (
        is_guide
        and booking.status is BookingStatus.PENDING
        and slot is not None
        and slot.start_at > datetime.utcnow()
    )

    can_cancel = (
        is_traveler
        or is_guide
    ) and booking.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED)

    # Determine if slot has started
    slot_started = slot is not None and slot.start_at <= datetime.utcnow()

    # Get timeline events
    timeline_events = db.session.scalars(
        select(BookingEvent)
        .where(BookingEvent.booking_id == booking.id)
        .order_by(BookingEvent.created_at.asc())
    ).all()

    # Format timeline for template
    timeline = []
    for event in timeline_events:
        # Determine action based on status transition
        if event.from_status is None:
            action = "Requested"
        elif event.from_status == BookingStatus.PENDING and event.to_status == BookingStatus.CONFIRMED:
            action = "Confirmed"
        elif event.from_status == BookingStatus.PENDING and event.to_status == BookingStatus.CANCELLED:
            action = "Cancelled"
        elif event.from_status == BookingStatus.CONFIRMED and event.to_status == BookingStatus.CANCELLED:
            action = "Cancelled"
        else:
            action = f"{event.from_status} to {event.to_status}"

        # Get actor name
        if event.actor_id is not None:
            actor = db.session.scalar(
                select(User.name).where(User.id == event.actor_id)
            ) or "Unknown"
        else:
            actor = "system"

        timeline.append({
            "action": action,
            "actor": actor,
            "timestamp": event.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return render_template(
        "guide/booking_detail.html",
        booking=booking,
        can_confirm=can_confirm,
        can_cancel=can_cancel,
        slot_started=slot_started,
        now=datetime.utcnow(),
        timeline=timeline,
    )
