from __future__ import annotations

from typing import Iterable, overload, Literal


DEFAULT_XSS_PATTERNS: tuple[str, ...] = (
    "<script",
    "</script",
    "<iframe",
    "</iframe",
    "<object",
    "<embed",
    "<svg",
    "<img",
    "javascript:",
    "vbscript:",
    "data:text/html",
    "onerror=",
    "onload=",
    "onclick=",
)

FORBIDDEN_URL_PROTOCOLS: tuple[str, ...] = ("javascript:", "data:", "file:")


def _has_xss(value: str, patterns: Iterable[str] = DEFAULT_XSS_PATTERNS) -> bool:
    lowered = value.lower()
    return any(pat in lowered for pat in patterns)


@overload
def validate_text_field(
    value: str | None,
    *,
    field_name: str,
    required: Literal[True],
    max_length: int | None = None,
    xss_patterns: Iterable[str] = DEFAULT_XSS_PATTERNS,
    invalid_message: str | None = None,
) -> str:
    pass


@overload
def validate_text_field(
    value: str | None,
    *,
    field_name: str,
    required: Literal[False] = False,
    max_length: int | None = None,
    xss_patterns: Iterable[str] = DEFAULT_XSS_PATTERNS,
    invalid_message: str | None = None,
) -> str | None:
    pass


def validate_text_field(
    value: str | None,
    *,
    field_name: str,
    required: bool = False,
    max_length: int | None = None,
    xss_patterns: Iterable[str] = DEFAULT_XSS_PATTERNS,
    invalid_message: str | None = None,
) -> str | None:
    if value is None:
        if required:
            raise ValueError(f"{field_name} darf nicht leer sein")
        return None

    stripped = value.strip()
    if not stripped:
        if required:
            raise ValueError(f"{field_name} darf nicht leer sein")
        return None

    if max_length is not None and len(stripped) > max_length:
        raise ValueError(f"{field_name} ist zu lang (max. {max_length} Zeichen)")

    if _has_xss(stripped, xss_patterns):
        if invalid_message:
            raise ValueError(invalid_message.format(field_name=field_name))
        raise ValueError(f"Ungültige Zeichen in {field_name}")

    return stripped


def validate_url_field(value: str | None, *, field_name: str = "Website") -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    if not (stripped.startswith("http://") or stripped.startswith("https://")):
        raise ValueError(f"{field_name} muss mit http:// oder https:// beginnen")
    lowered = stripped.lower()
    if any(proto in lowered for proto in FORBIDDEN_URL_PROTOCOLS):
        raise ValueError("Ungültiges URL-Protokoll")
    return stripped
