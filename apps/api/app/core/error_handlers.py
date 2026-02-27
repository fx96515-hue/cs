"""Standardized error handling for the application."""

from typing import Any, Dict, List, Union

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

import structlog

logger = structlog.get_logger(__name__)


class ErrorResponse:
    """Standard error response format."""

    @staticmethod
    def format_error(
        error_code: str,
        message: str,
        details: Union[Dict[str, Any], List[Any], None] = None,
        status_code: int = 500,
        detail: Any = None,
    ) -> JSONResponse:
        """Format error response consistently.

        Includes both the custom ``error`` envelope (for backward compatibility)
        and a top-level ``detail`` field (FastAPI-style) so that code relying on
        either format works correctly.
        """
        content: Dict[str, Any] = {
            "error": {
                "code": error_code,
                "message": message,
            }
        }

        if details:
            content["error"]["details"] = details

        # FastAPI-style top-level detail field
        content["detail"] = detail if detail is not None else message

        return JSONResponse(status_code=status_code, content=content)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning("validation_error", path=request.url.path, errors=exc.errors())

    # Ensure all error details are JSON serializable
    errors = []
    for error in exc.errors():
        error_dict = dict(error)
        # Convert any non-serializable objects to strings
        if "ctx" in error_dict and error_dict["ctx"]:
            error_dict["ctx"] = {k: str(v) for k, v in error_dict["ctx"].items()}
        errors.append(error_dict)

    return ErrorResponse.format_error(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details=errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=errors,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(
        "http_exception",
        path=request.url.path,
        status_code=exc.status_code,
        detail=str(exc.detail),
    )

    return ErrorResponse.format_error(
        error_code="HTTP_ERROR",
        message=str(exc.detail),
        status_code=exc.status_code,
        detail=exc.detail,
    )


async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """Handle database integrity errors."""
    logger.error("integrity_error", path=request.url.path, error=str(exc))

    # Parse the error to provide user-friendly message
    error_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)

    if "unique constraint" in error_msg.lower():
        message = "A record with this value already exists"
    elif "foreign key constraint" in error_msg.lower():
        message = "Referenced record does not exist"
    else:
        message = "Database constraint violation"

    return ErrorResponse.format_error(
        error_code="DATABASE_INTEGRITY_ERROR",
        message=message,
        status_code=status.HTTP_409_CONFLICT,
    )


async def operational_error_handler(
    request: Request, exc: OperationalError
) -> JSONResponse:
    """Handle database operational errors."""
    logger.error("operational_error", path=request.url.path, error=str(exc))

    return ErrorResponse.format_error(
        error_code="DATABASE_ERROR",
        message="A database error occurred. Please try again later.",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        "unexpected_error", path=request.url.path, error=str(exc), exc_info=True
    )

    return ErrorResponse.format_error(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
