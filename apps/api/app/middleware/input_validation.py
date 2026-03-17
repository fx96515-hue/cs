"""Input validation middleware for request sanitization."""

import json
import re
import logging
from typing import Any, Dict, Optional

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
        self.compiled_xss_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS
        ]

    def _check_sql_injection(self, value: str) -> bool:
        """Check if string contains SQL injection patterns."""
        return any(pattern.search(value) for pattern in self.sql_patterns)

    def _check_xss(self, value: str) -> bool:
        """Check if string contains XSS patterns."""
        return any(pattern.search(value) for pattern in self.compiled_xss_patterns)

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

    @staticmethod
    def _client_host(request: Request) -> str:
        return request.client.host if request.client else "unknown"

    @staticmethod
    def _is_write_method(request: Request) -> bool:
        return request.method in {"POST", "PUT", "PATCH"}

    @staticmethod
    def _is_json_request(request: Request) -> bool:
        return "application/json" in request.headers.get("content-type", "")

    @staticmethod
    def _parse_content_length(request: Request) -> Optional[int]:
        content_length = request.headers.get("content-length")
        if not content_length:
            return None
        return int(content_length)

    @staticmethod
    def _payload_too_large_response(content_size: int, host: str) -> Response:
        logger.warning(f"Request body too large: {content_size} bytes from {host}")
        from app.core.error_handlers import ErrorResponse

        return ErrorResponse.format_error(
            error_code="REQUEST_TOO_LARGE",
            message=f"Request body too large. Maximum size is {MAX_REQUEST_BODY_SIZE} bytes.",
            status_code=413,
        )

    @staticmethod
    def _malicious_input_response(host: str, path: str) -> Response:
        logger.warning(f"Malicious input detected from {host} to {path}")
        from app.core.error_handlers import ErrorResponse

        return ErrorResponse.format_error(
            error_code="MALICIOUS_INPUT",
            message="Invalid input detected. Request contains potentially malicious content.",
            status_code=400,
            detail=[{"msg": "Invalid characters in request body"}],
        )

    async def _validate_json_body(self, request: Request) -> Optional[Response]:
        host = self._client_host(request)
        body_bytes = await request.body()

        if len(body_bytes) > MAX_REQUEST_BODY_SIZE:
            return self._payload_too_large_response(len(body_bytes), host)

        if not body_bytes:
            return None

        try:
            body = json.loads(body_bytes)
        except Exception:
            # If JSON parsing fails, let FastAPI handle it.
            return None

        if isinstance(body, dict) and not self._validate_dict(body):
            return self._malicious_input_response(host, request.url.path)
        return None

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Validate request data."""
        if not self._is_write_method(request):
            return await call_next(request)

        try:
            host = self._client_host(request)
            content_length = self._parse_content_length(request)
            if content_length and content_length > MAX_REQUEST_BODY_SIZE:
                return self._payload_too_large_response(content_length, host)

            if self._is_json_request(request):
                validation_response = await self._validate_json_body(request)
                if validation_response is not None:
                    return validation_response
        except Exception:
            # If we can't read or validate safely, let FastAPI handle the request.
            pass

        return await call_next(request)
