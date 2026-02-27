from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from app.api.deps import get_current_user
from app.core.security import (
    verify_password,
    create_access_token,
    hash_password,
    generate_csrf_token,
)
from app.core.audit import AuditLogger
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.core.config import settings

from email_validator import validate_email, EmailNotValidError

router = APIRouter()
logger = structlog.get_logger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # Max 5 login attempts per minute
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        # Log failure with minimal info to prevent user enumeration via logs
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
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Check if user account is active
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
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
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
    token = create_access_token(sub=user.email, role=user.role)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/csrf-token")
def get_csrf_token(user: User = Depends(get_current_user)):
    """Generate and return a CSRF token for the authenticated user.

    This token should be included in the X-CSRF-Token header for
    state-changing operations (POST, PUT, PATCH, DELETE).
    """
    token = generate_csrf_token(user.email)
    return {"csrf_token": token}


# Dev-only bootstrap: creates admin if empty.
@router.post("/dev/bootstrap")
@limiter.limit("10/hour")  # Limit bootstrap attempts
def dev_bootstrap(request: Request, db: Session = Depends(get_db)):
    if db.query(User).count() > 0:
        return {"status": "skipped"}

    if not settings.BOOTSTRAP_ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BOOTSTRAP_ADMIN_PASSWORD is not set (configure it via .env)",
        )

    try:
        # Fail-fast on invalid emails (e.g. admin@local)
        validate_email(settings.BOOTSTRAP_ADMIN_EMAIL, check_deliverability=False)
    except EmailNotValidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid BOOTSTRAP_ADMIN_EMAIL: {e}",
        )

    admin = User(
        email=settings.BOOTSTRAP_ADMIN_EMAIL,
        password_hash=hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    return {"status": "created", "email": admin.email}
