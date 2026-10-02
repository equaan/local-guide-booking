"""Flask application factory for the Local Guide Booking System."""

from __future__ import annotations

import os

from flask import Flask, render_template

from app.blueprints.auth import auth_bp
from app.blueprints.guide import guide_bp
from app.blueprints.ops import ops_bp
from app.blueprints.slots import slots_bp
from app.config import BaseConfig, DevConfig, ProdConfig, TestConfig
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_class: type[BaseConfig] | None = None) -> Flask:
    """Create a configured app so tests and production get isolated state."""
    from app import models

    app = Flask(__name__)
    _ = models
    selected_config = config_class or _config_for_environment()
    selected_config.apply(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(guide_bp)
    app.register_blueprint(ops_bp)
    app.register_blueprint(slots_bp)

    @app.get("/")
    def home() -> str:
        return render_template("home.html")

    return app


def _config_for_environment() -> type[BaseConfig]:
    environment = os.getenv("APP_ENV", "dev")
    config_by_environment: dict[str, type[BaseConfig]] = {
        "dev": DevConfig,
        "test": TestConfig,
        "prod": ProdConfig,
    }
    return config_by_environment.get(environment, DevConfig)
