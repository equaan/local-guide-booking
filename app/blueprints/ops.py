"""Operational endpoints used by deployment health checks."""

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

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
