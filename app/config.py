"""Environment-backed configuration classes."""

from __future__ import annotations

import os

from flask import Flask


class BaseConfig:
    """Keep configuration in the environment for portable deployments."""

    @classmethod
    def apply(cls, app: Flask) -> None:
        app.config.from_mapping(
            APP_ENV=os.getenv("APP_ENV", "dev"),
            APP_VERSION=os.getenv("APP_VERSION", "dev"),
            DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///app.db"),
            GIT_SHA=os.getenv("GIT_SHA", "local"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            PORT=int(os.getenv("PORT", "8000")),
            SECRET_KEY=os.getenv("SECRET_KEY"),
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE="Lax",
            SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///app.db"),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )


class DevConfig(BaseConfig):
    """Development uses the environment supplied by the local operator."""


class TestConfig(BaseConfig):
    """Tests use a self-contained database and skip CSRF form validation."""

    @classmethod
    def apply(cls, app: Flask) -> None:
        super().apply(app)
        app.config.from_mapping(
            DATABASE_URL="sqlite://",
            SQLALCHEMY_DATABASE_URI="sqlite://",
            TESTING=True,
            WTF_CSRF_ENABLED=False,
        )


class ProdConfig(BaseConfig):
    """Production must fail closed instead of using a predictable session key."""

    @classmethod
    def apply(cls, app: Flask) -> None:
        super().apply(app)
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise RuntimeError("SECRET_KEY must be set in production")
        app.config["SECRET_KEY"] = secret_key
        app.config["SESSION_COOKIE_SECURE"] = True
