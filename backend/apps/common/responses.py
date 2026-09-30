from typing import Any, Dict, Optional

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.common.middleware import get_current_request_id


def api_success(
    data: Any = None,
    message: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK,
) -> Response:
    """Standardized API success response constructor.

    Payload format:
    {
      "success": true,
      "data": { ... },
      "meta": {
        "timestamp": "ISO-8601",
        "request_id": "...",
        ...
      }
    }
    """
    response_meta = {
        "timestamp": timezone.now().isoformat(),
        "request_id": get_current_request_id() or "-",
    }
    if meta:
        response_meta.update(meta)

    payload = {
        "success": True,
        "data": data if data is not None else {},
        "meta": response_meta,
    }
    if message:
        payload["message"] = message

    return Response(payload, status=status_code)


def api_error(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    request_id: Optional[str] = None,
) -> Response:
    """Standardized API error response constructor.

    Payload format:
    {
      "success": false,
      "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": { ... },
        "request_id": "..."
      },
      "meta": {
        "timestamp": "ISO-8601"
      }
    }
    """
    current_request_id = request_id or get_current_request_id() or "-"
    payload = {
        "success": False,
        "error": {
            "code": code.upper(),
            "message": message,
            "details": details or {},
            "request_id": current_request_id,
        },
        "meta": {
            "timestamp": timezone.now().isoformat(),
        },
    }
    return Response(payload, status=status_code)
