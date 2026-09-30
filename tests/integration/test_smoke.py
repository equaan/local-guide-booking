from __future__ import annotations


def test_health_returns_build_metadata(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"git_sha": "local", "status": "ok", "version": "dev"}


def test_ready_returns_success_when_database_is_available(client) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_home_returns_success(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert b"Find a local guide" in response.data
