from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, ExpiredSignatureError
import structlog

from app.core.security import decode_token
from app.core.audit import AuditLogger
from app.db.session import get_db
from app.models.user import User

logger = structlog.get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """Get current authenticated user with detailed error handling and logging."""
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        logger.warning(
            "auth.token_expired",
            ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentifizierung fehlgeschlagen",  # Generic message to prevent info disclosure
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.warning(
            "auth.invalid_token",
            error=str(e),
            ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentifizierung fehlgeschlagen",  # Generic message to prevent info disclosure
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("auth.unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentifizierungsfehler",
        )

    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user or not user.is_active:
        logger.warning(
            "auth.inactive_user",
            email=payload.get("sub"),
            exists=user is not None,
            active=user.is_active if user else False,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inaktiver Benutzer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(*roles: str):
    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            logger.warning(
                "auth.insufficient_role",
                user_email=user.email,
                user_role=user.role,
                required_roles=list(roles),
            )
            # Log permission denial for audit trail with specific role requirements
            action = f"role_check_failed_requires:{','.join(roles)}"
            AuditLogger.log_permission_denied(
                user=user,
                action=action,
                resource_type="endpoint",
                required_role=",".join(roles),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role"
            )
        return user

    return _check


# Alias for authenticated access without role check
# Returns dict with user info for endpoints that just need auth
def require_auth(user: User = Depends(get_current_user)) -> dict:
    """Require authenticated user (any role).

    Returns dict with user info for logging/audit purposes.
    This is a convenience wrapper around get_current_user that returns
    a dict instead of User object for endpoints using _: dict = Depends(require_auth).
    """
    return {"user": user, "email": user.email, "role": user.role}
