"""Extension instances initialised by the application factory."""

from flask import Request
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


@login_manager.request_loader
def load_anonymous_user(_request: Request) -> None:
    """Keep request authentication session-backed through Flask-Login."""
    return None


@login_manager.user_loader
def load_user(user_id: str):
    """Load the session user without exposing database details to routes."""
    from app.models import User

    return db.session.get(User, int(user_id))
