from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.forms import LoginForm, RegistrationForm
from app.models import User, UserRole

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing_user = db.session.scalar(
            db.select(User).where(func.lower(User.email) == email)
        )
        if existing_user is not None:
            form.email.errors.append("An account with that email already exists.")
        else:
            user = User(
                name=form.name.data.strip(),
                email=email,
                password_hash=generate_password_hash(form.password.data),
                role=UserRole(form.role.data),
                city=form.city.data.strip() or None,
                bio=form.bio.data.strip() or None,
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Registration successful.", "success")
            return redirect(url_for("home"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.scalar(db.select(User).where(User.email == email))
        if user is not None and check_password_hash(
            user.password_hash, form.password.data
        ):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("home"))
        flash("Invalid email or password.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))
