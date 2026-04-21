"""ASGI entrypoint for local runs: ``cd apps/api && uvicorn main:app --reload``."""

from aistruth_api.main import app

__all__ = ["app"]
