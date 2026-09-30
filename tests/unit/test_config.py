from __future__ import annotations

import pytest

from app import create_app
from app.config import ProdConfig


def test_prod_config_rejects_the_default_missing_secret_key(monkeypatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="must be set"):
        create_app(ProdConfig)
