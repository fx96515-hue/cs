import re
from pydantic import BaseModel, EmailStr, Field, field_validator

# Special characters required in passwords
SPECIAL_CHARS_PATTERN = r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/;'`~]"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password", mode="before")
    @classmethod
    def password_not_common(cls, v: object) -> object:
        """Check password strength - comprehensive validation.

        For production: integrate with HaveIBeenPwned API or similar service.
        """
        # Extended list of common passwords
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
        # Only apply string checks when the value is actually a string
        if not isinstance(v, str):
            return v
        if v.lower() in common:
            raise ValueError("Passwort ist zu schwach und leicht zu erraten")

        # Check for complexity requirements
        if not re.search(r"[A-Z]", v):
            raise ValueError("Passwort muss mindestens einen Großbuchstaben enthalten")
        if not re.search(r"[a-z]", v):
            raise ValueError("Passwort muss mindestens einen Kleinbuchstaben enthalten")
        if not re.search(r"\d", v):
            raise ValueError("Passwort muss mindestens eine Ziffer enthalten")
        if not re.search(SPECIAL_CHARS_PATTERN, v):
            raise ValueError("Passwort muss mindestens ein Sonderzeichen enthalten")

        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True
