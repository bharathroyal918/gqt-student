import uuid
from contextvars import ContextVar
from typing import Optional

_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_current_request_id() -> Optional[str]:
    """Retrieve the current request's unique ID from contextvars."""
    return _request_id_ctx.get()


class RequestIDMiddleware:
    """Middleware that assigns a unique UUID to every incoming HTTP request.

    - Extracts 'X-Request-ID' header if present; otherwise generates a new UUID4.
    - Sets request.id and contextvar for structured logging.
    - Adds 'X-Request-ID' to the outgoing response headers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        request.id = request_id
        token = _request_id_ctx.set(request_id)

        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            return response
        finally:
            _request_id_ctx.reset(token)
