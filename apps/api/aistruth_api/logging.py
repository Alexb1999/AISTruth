from __future__ import annotations

import logging.config
import uuid
from collections.abc import Awaitable, Callable

from pythonjsonlogger.json import JsonFormatter
from starlette.requests import Request
from starlette.responses import Response


class RequestIdJsonFormatter(JsonFormatter):
    def process_log_record(self, log_record: dict[str, object]) -> dict[str, object]:
        log_record.setdefault("service", "aistruth-api")
        return super().process_log_record(log_record)


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": RequestIdJsonFormatter,
                    "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "root": {"handlers": ["default"], "level": "INFO"},
        }
    )


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
