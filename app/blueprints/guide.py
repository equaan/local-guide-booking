from __future__ import annotations

from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import SlotForm
from app.models import Slot, UserRole
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
