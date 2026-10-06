from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db


def test_health_returns_build_metadata(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"git_sha": "local", "status": "ok", "version": "dev"}


def test_ready_returns_success_when_database_is_available(client) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_ready_returns_service_unavailable_when_database_query_fails(
    client, monkeypatch
) -> None:
    def raise_database_error(*_args, **_kwargs):
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(db.session, "execute", raise_database_error)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.get_json() == {"status": "not ready"}


def test_home_returns_success(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert b"Find a local guide" in response.data
