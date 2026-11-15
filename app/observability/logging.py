import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.observability.context import request_id_context


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        for field in (
            "event",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "error_type",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RequestContextFilter())
    handler.setFormatter(JsonLogFormatter())
    logging.basicConfig(level=level.upper(), handlers=[handler], force=True)
