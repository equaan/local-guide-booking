"""WSGI entry point for local development and Gunicorn."""

from app import create_app

app = create_app()
