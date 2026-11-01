import logging

from django.conf import settings
from django.http import Http404
from rest_framework import status as http_status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("api")


class ApiError(APIException):
    """Raise an API error with an explicit status code, machine code and message.

    Example: ``raise ApiError(409, "invalid_state", "Job is closed", {"status": "closed"})``.
    """

    def __init__(self, status_code, code, message, details=None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details if details is not None else {}
        super().__init__(detail=message)


def _envelope(code, message, details):
    return {"error": {"code": code, "message": message, "details": details or {}}}


def exception_handler(exc, context):
    # ApiError: use its own code/message/details.
    if isinstance(exc, ApiError):
        return Response(
            _envelope(exc.code, exc.message, exc.details),
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            return Response(
                _envelope(
                    "validation_error",
                    "The request data is invalid.",
                    response.data,
                ),
                status=response.status_code,
            )
        if isinstance(exc, NotAuthenticated):
            return Response(
                _envelope("not_authenticated", "Authentication is required.", {}),
                status=response.status_code,
            )
        if isinstance(exc, AuthenticationFailed):
            return Response(
                _envelope("authentication_failed", str(exc.detail), {}),
                status=response.status_code,
            )
        if isinstance(exc, PermissionDenied):
            return Response(
                _envelope("forbidden", "You do not have permission to do this.", {}),
                status=response.status_code,
            )
        if isinstance(exc, (NotFound, Http404)):
            return Response(
                _envelope("not_found", "Resource not found.", {}),
                status=http_status.HTTP_404_NOT_FOUND,
            )
        # Any other handled DRF exception: wrap generically.
        message = response.data.get("detail") if isinstance(response.data, dict) else None
        return Response(
            _envelope("error", str(message or "Request failed."), {}),
            status=response.status_code,
        )

    # Unhandled exception.
    logger.exception("Unhandled exception in API request")
    if settings.DEBUG:
        # Let Django surface the traceback in development.
        return None
    return Response(
        _envelope("internal_error", "An unexpected error occurred.", {}),
        status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
