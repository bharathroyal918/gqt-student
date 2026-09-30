import logging
import uuid

from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class DomainException(APIException):
    """Base domain exception for service layer business rule failures."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "DOMAIN_ERROR"
    default_detail = "A business domain rule has been violated."

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code:
            self.status_code = status_code
        super().__init__(detail=detail, code=code)


class ModuleLockedException(DomainException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_code = "MODULE_LOCKED"
    default_detail = "This learning module is locked until prerequisites are met."


def custom_exception_handler(exc, context):
    """Standardized centralized error response handler for all DRF exceptions."""
    response = exception_handler(exc, context)
    request_id = str(uuid.uuid4())
    current_time = timezone.now().isoformat()

    if response is not None:
        error_code = getattr(exc, "default_code", "ERROR")
        if hasattr(exc, "get_codes") and isinstance(exc.get_codes(), str):
            error_code = exc.get_codes()

        details = response.data
        message = "An error occurred while processing your request."

        if isinstance(details, dict):
            if "detail" in details:
                message = str(details.pop("detail"))
        elif isinstance(details, list) and len(details) > 0:
            message = str(details[0])

        formatted_error = {
            "success": False,
            "error": {
                "code": str(error_code).upper(),
                "message": message,
                "details": details if details else {},
                "request_id": request_id,
            },
            "meta": {
                "timestamp": current_time,
            },
        }
        response.data = formatted_error
        return response

    # Catch unhandled server exceptions (500)
    logger.exception(f"Unhandled Server Error [request_id={request_id}]: {exc}", exc_info=exc)
    return Response(
        {
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": {},
                "request_id": request_id,
            },
            "meta": {
                "timestamp": current_time,
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
