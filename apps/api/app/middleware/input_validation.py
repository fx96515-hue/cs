"""Input validation middleware for request sanitization."""

import re
import logging
from typing import Any, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Maximum request body size: 10MB
MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests."""

    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bEXEC\b\()",
        r"(\bEXECUTE\b\()",
        r"(;.*(-{2}|\/\*))",  # SQL comment patterns
        r"('\s*(OR|AND)\s*'?\d)",  # Basic OR/AND injection
        r"'\s*--",  # SQL comment after quote
        r"\bWAITFOR\b.*\bDELAY\b",  # Time-based blind SQL injection
        r"\bSLEEP\b\s*\(",  # MySQL SLEEP function
        r"\bBENCHMARK\b\s*\(",  # MySQL BENCHMARK function
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers like onclick=
    ]

    def __init__(self, app: Any):
        """Initialize middleware."""
        super().__init__(app)
        self.sql_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS
        ]
        self.xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]

    def _check_sql_injection(self, value: str) -> bool:
        """Check if string contains SQL injection patterns."""
        return any(pattern.search(value) for pattern in self.sql_patterns)

    def _check_xss(self, value: str) -> bool:
        """Check if string contains XSS patterns."""
        return any(pattern.search(value) for pattern in self.xss_patterns)

    def _validate_value(self, value: Any) -> bool:
        """Validate a single value."""
        if isinstance(value, str):
            if self._check_sql_injection(value):
                return False
            if self._check_xss(value):
                return False
        elif isinstance(value, dict):
            return self._validate_dict(value)
        elif isinstance(value, list):
            return all(self._validate_value(item) for item in value)
        return True

    def _validate_dict(self, data: Dict[str, Any]) -> bool:
        """Validate all values in a dictionary."""
        for value in data.values():
            if not self._validate_value(value):
                return False
        return True

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Validate request data."""
        # Skip validation for GET requests (query params handled by FastAPI)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Check Content-Length header for body size limit
                content_length = request.headers.get("content-length")
                if content_length and int(content_length) > MAX_REQUEST_BODY_SIZE:
                    logger.warning(
                        f"Request body too large: {content_length} bytes from {request.client.host if request.client else 'unknown'}"
                    )
                    from app.core.error_handlers import ErrorResponse

                    return ErrorResponse.format_error(
                        error_code="REQUEST_TOO_LARGE",
                        message=f"Request body too large. Maximum size is {MAX_REQUEST_BODY_SIZE} bytes.",
                        status_code=413,
                    )

                if "application/json" in request.headers.get("content-type", ""):
                    # Read the body as bytes to avoid consuming the stream
                    body_bytes = await request.body()

                    # Double-check actual body size
                    if len(body_bytes) > MAX_REQUEST_BODY_SIZE:
                        logger.warning(
                            f"Request body too large: {len(body_bytes)} bytes from {request.client.host if request.client else 'unknown'}"
                        )
                        from app.core.error_handlers import ErrorResponse

                        return ErrorResponse.format_error(
                            error_code="REQUEST_TOO_LARGE",
                            message=f"Request body too large. Maximum size is {MAX_REQUEST_BODY_SIZE} bytes.",
                            status_code=413,
                        )

                    if body_bytes:
                        try:
                            body = __import__("json").loads(body_bytes)
                            if not self._validate_dict(body):
                                logger.warning(
                                    f"Malicious input detected from {request.client.host if request.client else 'unknown'} "
                                    f"to {request.url.path}"
                                )
                                from app.core.error_handlers import ErrorResponse

                                return ErrorResponse.format_error(
                                    error_code="MALICIOUS_INPUT",
                                    message="Invalid input detected. Request contains potentially malicious content.",
                                    status_code=400,
                                    detail=[
                                        {"msg": "Invalid characters in request body"}
                                    ],
                                )
                        except Exception:
                            # If JSON parsing fails, let FastAPI handle it
                            pass
            except Exception:
                # If we can't read the body, let FastAPI handle it
                pass

        response: Response = await call_next(request)
        return response
