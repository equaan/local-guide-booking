from __future__ import annotations

from flask import Blueprint, abort, jsonify, render_template, request

from app.forms import BookingRequestForm
from app.models import BookingStatus
from app.services.slots import get_public_slot, list_public_slots
from app.timeutils import now_ist

slots_bp = Blueprint("slots", __name__)


def _filters() -> tuple[str | None, str | None]:
    city = request.args.get("city", "").strip() or None
    slot_date = request.args.get("date", "").strip() or None
    return city, slot_date


@slots_bp.get("/slots")
def list_slots():
    city, slot_date = _filters()
    return render_template(
        "slots/list.html",
        slots=list_public_slots(city=city, slot_date=slot_date),
        city=city or "",
        slot_date=slot_date or "",
    )


@slots_bp.get("/slots/<int:slot_id>")
def slot_detail(slot_id: int):
    slot = get_public_slot(slot_id)
    if slot is None:
        abort(404)
    available = slot.is_active and slot.start_at > now_ist()
    available = available and not any(
        booking.status is BookingStatus.CONFIRMED for booking in slot.bookings
    )
    return render_template(
        "slots/detail.html",
        slot=slot,
        available=available,
        booking_form=BookingRequestForm(),
    )


@slots_bp.get("/api/v1/slots")
def slots_api():
    city, slot_date = _filters()
    slots = list_public_slots(city=city, slot_date=slot_date)
    return jsonify(
        slots=[
            {
                "id": slot.id,
                "title": slot.title,
                "guide": slot.guide.name,
                "city": slot.guide.city,
                "start_at": slot.start_at.isoformat(),
                "end_at": slot.end_at.isoformat(),
                "price_inr": slot.price_inr,
            }
            for slot in slots
        ]
    )
