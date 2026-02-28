from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.password_policy import validate_password_policy


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password", mode="before")
    @classmethod
    def password_not_common(cls, v: object) -> object:
        """Check password strength - comprehensive validation.

        For production: integrate with HaveIBeenPwned API or similar service.
        """
        # Only apply string checks when the value is actually a string
        if not isinstance(v, str):
            return v
        validate_password_policy(v)
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
