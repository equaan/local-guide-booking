from __future__ import annotations

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()
