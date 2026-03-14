from __future__ import annotations

from typing import Annotated

import structlog
from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.audit import AuditLogger
from app.core.config import settings
from app.core.password_policy import validate_password_policy
from app.core.security import (
    create_access_token,
    generate_csrf_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut

router = APIRouter()
logger = structlog.get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)
INVALID_CREDENTIALS_DETAIL = "Invalid credentials"


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure(),
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.auth_cookie_secure(),
        samesite="lax",
        path="/",
    )


@router.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        logger.warning(
            "auth.login_failed",
            email=payload.email,
            ip=ip_address,
            user_agent=user_agent,
        )

        AuditLogger.log_auth_event(
            email=payload.email,
            event_type="login_failed",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            reason="Invalid credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_DETAIL,
        )

    if not user.is_active:
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        logger.warning(
            "auth.inactive_user_login_attempt", email=user.email, ip=ip_address
        )

        AuditLogger.log_auth_event(
            email=user.email,
            event_type="login_failed",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            reason="Inactive account",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_DETAIL,
        )

    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logger.info("auth.login_success", email=user.email, role=user.role, ip=ip_address)
    AuditLogger.log_auth_event(
        email=user.email,
        event_type="login_success",
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
    )

    token = create_access_token(
        sub=user.email,
        role=user.role,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    _set_auth_cookie(response, token)
    return TokenResponse(access_token=token)


@router.get("/me")
def me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return UserOut.model_validate(user)


@router.get("/csrf-token")
def get_csrf_token(user: Annotated[User, Depends(get_current_user)]) -> dict:
    """Generate and return a CSRF token for the authenticated user."""
    token = generate_csrf_token(user.email)
    return {"csrf_token": token}


@router.post("/refresh")
def refresh_access_token(
    request: Request,
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
) -> TokenResponse:
    ip_address = request.client.host if request.client else "unknown"
    logger.info("auth.refresh_success", email=user.email, ip=ip_address)
    token = create_access_token(
        sub=user.email,
        role=user.role,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    _set_auth_cookie(response, token)
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    _clear_auth_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/dev/bootstrap")
@limiter.limit("10/hour")
def dev_bootstrap(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if settings.APP_ENV not in {"dev", "test"}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    if not settings.BOOTSTRAP_ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BOOTSTRAP_ADMIN_PASSWORD is not set (configure it via .env)",
        )

    try:
        validate_password_policy(settings.BOOTSTRAP_ADMIN_PASSWORD)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    try:
        validate_email(settings.BOOTSTRAP_ADMIN_EMAIL, check_deliverability=False)
    except EmailNotValidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid BOOTSTRAP_ADMIN_EMAIL: {e}",
        ) from e

    admin = db.query(User).filter(User.email == settings.BOOTSTRAP_ADMIN_EMAIL).first()
    if admin:
        admin.password_hash = hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD)
        admin.is_active = True
        admin.role = "admin"
        db.commit()
        return {"status": "updated", "email": admin.email}

    admin = User(
        email=settings.BOOTSTRAP_ADMIN_EMAIL,
        password_hash=hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    return {"status": "created", "email": admin.email}
