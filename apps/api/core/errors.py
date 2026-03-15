"""
Custom error handling for the API.

Implements the standard error format per section 3.5:
{
  "detail": "Human-readable message",
  "code": "RESOURCE_NOT_FOUND",
  "status": 404
}
"""
import logging
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    """Standard error codes for the Learning Space API."""

    # General errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"

    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_PROCESSING_FAILED = "RESOURCE_PROCESSING_FAILED"

    # Account management errors
    CANNOT_UNLINK_LAST_ACCOUNT = "CANNOT_UNLINK_LAST_ACCOUNT"
    ACCOUNT_ALREADY_LINKED = "ACCOUNT_ALREADY_LINKED"
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    PROVIDER_NOT_SUPPORTED = "PROVIDER_NOT_SUPPORTED"

    # Graph/Knowledge base errors
    TAG_NOT_FOUND = "TAG_NOT_FOUND"
    GRAPH_UPDATE_FAILED = "GRAPH_UPDATE_FAILED"

    # Chat/Agent errors
    CONVERSATION_NOT_FOUND = "CONVERSATION_NOT_FOUND"
    AGENT_ERROR = "AGENT_ERROR"


class APIError(HTTPException):
    """Custom API exception that follows the standard error format."""

    def __init__(
        self,
        detail: str,
        code: ErrorCode,
        status_code: int,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code


class ValidationError(APIError):
    """Validation error (400)."""

    def __init__(self, detail: str, code: ErrorCode = ErrorCode.VALIDATION_ERROR):
        super().__init__(
            detail=detail, code=code, status_code=status.HTTP_400_BAD_REQUEST
        )


class UnauthorizedError(APIError):
    """Authentication required (401)."""

    def __init__(
        self,
        detail: str = "Authentication required",
        code: ErrorCode = ErrorCode.UNAUTHORIZED
    ):
        super().__init__(
            detail=detail, code=code, status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenError(APIError):
    """Access forbidden (403)."""

    def __init__(
        self,
        detail: str = "Access forbidden",
        code: ErrorCode = ErrorCode.FORBIDDEN
    ):
        super().__init__(
            detail=detail, code=code, status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(APIError):
    """Resource not found (404)."""

    def __init__(
        self, detail: str, code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND
    ):
        super().__init__(
            detail=detail, code=code, status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictError(APIError):
    """Resource conflict (409)."""

    def __init__(self, detail: str, code: ErrorCode):
        super().__init__(detail=detail, code=code, status_code=status.HTTP_409_CONFLICT)


class RateLimitError(APIError):
    """Rate limit exceeded (429)."""

    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        code: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED
    ):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class InternalServerError(APIError):
    """Internal server error (500)."""

    def __init__(
        self,
        detail: str = "Internal server error",
        code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR
    ):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Specific error instances for common cases
def resource_not_found(
    resource_type: str = "Resource", resource_id: str = None
) -> NotFoundError:
    """Create a resource not found error."""
    detail = f"{resource_type} not found"
    if resource_id:
        detail += f": {resource_id}"
    return NotFoundError(detail)


def cannot_unlink_last_account() -> ValidationError:
    """Error when trying to unlink the user's last account."""
    return ValidationError(
        "Cannot unlink the last account. Users must have at least one linked account.",
        code=ErrorCode.CANNOT_UNLINK_LAST_ACCOUNT
    )


def account_already_linked() -> ConflictError:
    """Error when trying to link an account that's already linked to another user."""
    return ConflictError(
        "This account is already linked to another user.",
        code=ErrorCode.ACCOUNT_ALREADY_LINKED
    )


async def api_exception_handler(request: Request, exc: APIError) -> JSONResponse:
    """Custom exception handler for APIError instances."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.code,
            "status": exc.status_code
        }
    )


async def http_exception_wrapper(request: Request, exc: HTTPException) -> JSONResponse:
    """Wrap standard HTTPException to match our error format."""
    # For standard HTTPExceptions that aren't our custom APIError
    if not isinstance(exc, APIError):
        # Map common HTTP status codes to our error codes
        error_code_map = {
            400: ErrorCode.VALIDATION_ERROR,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.RESOURCE_NOT_FOUND,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.INTERNAL_SERVER_ERROR,
        }

        code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": code,
                "status": exc.status_code
            }
        )

    # If it's already an APIError, use the original handler
    return await api_exception_handler(request, exc)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with our standard error format."""
    # Log the exception for debugging
    logger = logging.getLogger(__name__)
    logger.exception("Unhandled exception: %s", exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "code": ErrorCode.INTERNAL_SERVER_ERROR,
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )
