from __future__ import annotations

import re


SPECIAL_CHARS_PATTERN = r"[!@#$%^&*(),.?\":{}|<>_+=\[\]\\\/;'`~-]"


def validate_password_policy(password: str) -> None:
    """Validate password strength and common-password checks."""
    common = [
        "password",
        "12345678",
        "admin123",
        "qwerty",
        "letmein",
        "welcome",
        "monkey",
        "1234567890",
        "abc123",
        "password1",
        "password123",
        "qwerty123",
        "welcome1",
        "admin",
        "administrator",
        "root",
        "toor",
        "pass",
        "test",
        "guest",
        "user",
        "demo",
        "sample",
        "changeme",
        "default",
    ]

    if password.lower() in common:
        raise ValueError("Passwort ist zu schwach und leicht zu erraten")

    if len(password) < 8:
        raise ValueError("Passwort muss mindestens 8 Zeichen haben")
    if len(password) > 128:
        raise ValueError("Passwort darf maximal 128 Zeichen haben")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Passwort muss mindestens einen Großbuchstaben enthalten")
    if not re.search(r"[a-z]", password):
        raise ValueError("Passwort muss mindestens einen Kleinbuchstaben enthalten")
    if not re.search(r"\d", password):
        raise ValueError("Passwort muss mindestens eine Ziffer enthalten")
    if not re.search(SPECIAL_CHARS_PATTERN, password):
        raise ValueError("Passwort muss mindestens ein Sonderzeichen enthalten")
