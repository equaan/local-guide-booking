"""Flask application factory for the Local Guide Booking System."""

from __future__ import annotations

import logging
import os
import sys
from time import perf_counter

from flask import Flask, Response, g, render_template, request
from flask.logging import default_handler

from app.blueprints.auth import auth_bp
from app.blueprints.bookings import bookings_bp
from app.blueprints.guide import guide_bp
from app.blueprints.ops import ops_bp
from app.blueprints.slots import slots_bp
from app.config import BaseConfig, DevConfig, ProdConfig, TestConfig
from app.extensions import csrf, db, login_manager, migrate
from app.metrics import http_request_duration, http_requests


def create_app(config_class: type[BaseConfig] | None = None) -> Flask:
    """Create a configured app so tests and production get isolated state."""
    from app import models

    app = Flask(__name__)
    _ = models
    selected_config = config_class or _config_for_environment()
    selected_config.apply(app)
    _configure_logging(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(guide_bp)
    app.register_blueprint(ops_bp)
    app.register_blueprint(slots_bp)

    @app.before_request
    def start_request_timer() -> None:
        g.request_started_at = perf_counter()

    @app.after_request
    def observe_request(response: Response) -> Response:
        duration_seconds = perf_counter() - getattr(
            g, "request_started_at", perf_counter()
        )
        endpoint = request.url_rule.rule if request.url_rule else "unmatched"
        http_requests.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code),
        ).inc()
        http_request_duration.labels(endpoint=endpoint).observe(duration_seconds)
        app.logger.info(
            "request method=%s path=%s status=%s duration_ms=%.2f",
            request.method,
            request.path,
            response.status_code,
            duration_seconds * 1000,
        )
        return response

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


def _configure_logging(app: Flask) -> None:
    """Send request logs to stdout without retaining Flask's stderr handler."""
    app.logger.removeHandler(default_handler)
    if not any(
        getattr(handler, "_lgb_stdout", False) for handler in app.logger.handlers
    ):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        handler._lgb_stdout = True
        app.logger.addHandler(handler)
    app.logger.setLevel(app.config["LOG_LEVEL"])
