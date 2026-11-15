import logging
import time
from uuid import UUID, uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.observability.context import request_id_context

logger = logging.getLogger("app.http")
REQUEST_ID_HEADER = b"x-request-id"


def _request_id(scope: Scope) -> str:
    for header_name, header_value in scope.get("headers", []):
        if header_name.lower() != REQUEST_ID_HEADER:
            continue
        try:
            return str(UUID(header_value.decode("ascii")))
        except (UnicodeDecodeError, ValueError):
            break
    return str(uuid4())


class RequestObservabilityMiddleware:
    """Attach a request ID and emit a body-free structured completion log."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    def __getattr__(self, name: str):
        # Keep FastAPI attributes such as `openapi` and `dependency_overrides` available.
        return getattr(self.app, name)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _request_id(scope)
        context_token = request_id_context.set(request_id)
        scope.setdefault("state", {})["request_id"] = request_id
        started_at = time.perf_counter()
        status_code = 500
        error_type: str | None = None

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != REQUEST_ID_HEADER
                ]
                headers.append((REQUEST_ID_HEADER, request_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception as exc:
            error_type = type(exc).__name__
            raise
        finally:
            route = scope.get("route")
            path = getattr(route, "path", scope.get("path", ""))
            duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
            level = logging.ERROR if status_code >= 500 or error_type else (
                logging.WARNING if status_code >= 400 else logging.INFO
            )
            logger.log(
                level,
                "http_request_complete",
                extra={
                    "event": "http_request_complete",
                    "method": scope.get("method", ""),
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "error_type": error_type,
                },
            )
            request_id_context.reset(context_token)
