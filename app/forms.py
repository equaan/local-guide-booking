from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


class RegistrationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=128)]
    )
    role = SelectField(
        "Role",
        choices=[("traveler", "Traveler"), ("guide", "Guide")],
        validators=[DataRequired()],
    )
    city = StringField("City", validators=[Optional(), Length(max=80)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Register")

    def validate(self, extra_validators=None) -> bool:
        is_valid = super().validate(extra_validators=extra_validators)
        if self.role.data == "guide" and not self.city.data.strip():
            self.city.errors.append("City is required for guides.")
            is_valid = False
        return is_valid


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class SlotForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    start_at = StringField("Start time", validators=[DataRequired()])
    end_at = StringField("End time", validators=[DataRequired()])
    price_inr = IntegerField(
        "Price (INR)", validators=[DataRequired(), NumberRange(min=0)]
    )
    submit = SubmitField("Create slot")
