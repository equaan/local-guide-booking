"""Operational endpoints used by deployment health checks."""

from flask import Blueprint, Response, current_app, jsonify
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.metrics import refresh_bookings_current, registry

ops_bp = Blueprint("ops", __name__)


@ops_bp.get("/health")
def health():
    """Report liveness without depending on database availability."""
    return jsonify(
        status="ok",
        version=current_app.config["APP_VERSION"],
        git_sha=current_app.config["GIT_SHA"],
    )


@ops_bp.get("/ready")
def ready():
    """Report database readiness independently from liveness."""
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(status="not ready"), 503
    return jsonify(status="ready")


@ops_bp.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics and calculate current booking counts per scrape."""
    refresh_bookings_current()
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)
