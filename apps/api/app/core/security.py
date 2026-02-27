from datetime import datetime, timedelta, timezone
import secrets
import hashlib

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

"""Security primitives.

We use argon2 for password hashing instead of bcrypt or pbkdf2.

Reason:
- passlib+bcrypt can break in container builds when bcrypt's internal version
  metadata layout changes (e.g. bcrypt 4.x removed bcrypt.__about__).
- argon2 is the winner of the Password Hashing Competition (PHC).
- argon2-cffi compiles cleanly on all platforms (Windows, Linux, Alpine, Slim).
- OWASP recommends argon2id as the first choice for password hashing.

NOTE:
- This is a local/dev product, but we still use a strong KDF and fail-fast
  if required secrets are missing.
- We use argon2id variant with OWASP-recommended parameters:
  - memory_cost: 64 MB (65536 KiB)
  - time_cost: 3 iterations
  - parallelism: 4 threads
- We support pbkdf2_sha256 for backward compatibility (marked as deprecated).
  Old hashes will still verify, but new hashes will use argon2.
"""

# Using argon2 with secure OWASP-recommended parameters.
# pbkdf2_sha256 is supported for backward compatibility but deprecated.
pwd_context = CryptContext(
    schemes=["argon2", "pbkdf2_sha256"],
    deprecated=["pbkdf2_sha256"],
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,  # 3 iterations
    argon2__parallelism=4,  # 4 threads
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(sub: str, role: str, expires_minutes: int = 60 * 24) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "sub": sub,
        "role": role,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=["HS256"],
        audience=settings.JWT_AUDIENCE,
        issuer=settings.JWT_ISSUER,
    )


# CSRF Token Management
# Store for CSRF tokens in memory (in production, use Redis or database)
_csrf_tokens: dict[str, dict] = {}


def generate_csrf_token(session_id: str) -> str:
    """Generate a CSRF token for a session.

    Args:
        session_id: Unique session identifier (e.g., user email or session UUID)

    Returns:
        CSRF token string
    """
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Store hashed token with expiration (1 hour)
    _csrf_tokens[session_id] = {
        "hash": token_hash,
        "expires": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    return token


def validate_csrf_token(session_id: str, token: str) -> bool:
    """Validate a CSRF token for a session.

    Args:
        session_id: Session identifier
        token: CSRF token to validate

    Returns:
        True if token is valid, False otherwise
    """
    if session_id not in _csrf_tokens:
        return False

    stored = _csrf_tokens[session_id]

    # Check if token has expired
    if datetime.now(timezone.utc) > stored["expires"]:
        # Clean up expired token
        del _csrf_tokens[session_id]
        return False

    # Validate token hash
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token_hash == stored["hash"]


def cleanup_expired_csrf_tokens() -> None:
    """Remove expired CSRF tokens from storage."""
    now = datetime.now(timezone.utc)
    expired_sessions = [
        session_id for session_id, data in _csrf_tokens.items() if now > data["expires"]
    ]
    for session_id in expired_sessions:
        del _csrf_tokens[session_id]
