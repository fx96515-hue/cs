"""Tests for error handlers."""

import pytest
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from app.core.error_handlers import (
    ErrorResponse,
    validation_exception_handler,
    http_exception_handler,
    integrity_error_handler,
    operational_error_handler,
    generic_exception_handler,
)
from typing import Any, cast


def test_error_response_format_basic():
    """Test basic error response formatting."""
    response = ErrorResponse.format_error(
        error_code="TEST_ERROR", message="Test error message", status_code=400
    )

    assert response.status_code == 400
    body = response.body
    json_content = (
        body.decode() if isinstance(body, (bytes, bytearray)) else bytes(body).decode()
    )
    assert "TEST_ERROR" in json_content
    assert "Test error message" in json_content


def test_error_response_format_with_details():
    """Test error response with details."""
    details = {"field": "email", "issue": "invalid format"}
    response = ErrorResponse.format_error(
        error_code="VALIDATION_ERROR",
        message="Validation failed",
        details=details,
        status_code=422,
    )

    assert response.status_code == 422
    body = response.body
    json_content = (
        body.decode() if isinstance(body, (bytes, bytearray)) else bytes(body).decode()
    )
    assert "VALIDATION_ERROR" in json_content
    assert "field" in json_content


def test_error_response_default_status():
    """Test error response with default status code."""
    response = ErrorResponse.format_error(
        error_code="INTERNAL_ERROR", message="Something went wrong"
    )

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_validation_exception_handler():
    """Test validation exception handler."""
    # Create a mock validation error
    from pydantic import BaseModel, ValidationError

    class TestModel(BaseModel):
        email: str

    try:
        TestModel(email=cast(Any, 123))  # Invalid email type
    except ValidationError as e:
        request = type("MockRequest", (), {"url": type("URL", (), {"path": "/test"})})()
        exc = RequestValidationError(errors=e.errors())

        response = await validation_exception_handler(request, exc)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_http_exception_handler():
    """Test HTTP exception handler."""
    request = type("MockRequest", (), {"url": type("URL", (), {"path": "/test"})})()
    exc = StarletteHTTPException(status_code=404, detail="Not found")

    response = await http_exception_handler(request, exc)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_integrity_error_handler():
    """Test integrity error handler."""
    request = type("MockRequest", (), {"url": type("URL", (), {"path": "/test"})})()
    exc = IntegrityError("statement", "params", Exception("orig"))

    response = await integrity_error_handler(request, exc)

    assert response.status_code in [400, 409]


@pytest.mark.asyncio
async def test_operational_error_handler():
    """Test operational error handler."""
    request = type("MockRequest", (), {"url": type("URL", (), {"path": "/test"})})()
    exc = OperationalError("statement", "params", Exception("orig"))

    response = await operational_error_handler(request, exc)

    assert response.status_code in [500, 503]


@pytest.mark.asyncio
async def test_generic_exception_handler():
    """Test generic exception handler."""
    request = type("MockRequest", (), {"url": type("URL", (), {"path": "/test"})})()
    exc = Exception("Generic error")

    response = await generic_exception_handler(request, exc)

    assert response.status_code == 500
