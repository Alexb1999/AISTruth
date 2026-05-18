"""ASGI entrypoint for local runs: ``cd backend && uvicorn main:app --reload``."""

from aistruth_api.main import app

__all__ = ["app"]
