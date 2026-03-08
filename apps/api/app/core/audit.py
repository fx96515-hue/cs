"""Audit logging for tracking all data modifications."""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

import structlog

from app.models.user import User
from app.models.audit_log import AuditLog

logger = structlog.get_logger(__name__)


def _to_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(v) for v in value]
    return str(value)


class AuditLogger:
    """Log all CRUD operations for audit trail."""

    @staticmethod
    def _persist(
        db: Session,
        *,
        action: str,
        user: User | None,
        entity_type: str | None,
        entity_id: int | None,
        payload: Dict[str, Any] | None,
        request_id: Optional[str] = None,
    ) -> None:
        try:
            safe_payload = _to_json_safe(payload) if payload is not None else None
            entry = AuditLog(
                actor_id=user.id if user else None,
                actor_email=user.email if user else None,
                actor_role=user.role if user else None,
                action=action,
                entity_type=entity_type or "unknown",
                entity_id=entity_id,
                request_id=request_id,
                payload=safe_payload,
                created_at=datetime.utcnow(),
            )
            db.add(entry)
            db.commit()
        except Exception as exc:  # pragma: no cover - audit must not break flow
            logger.warning("audit.persist_failed", error=str(exc))

    @staticmethod
    def log_create(
        db: Session,
        user: User,
        entity_type: str,
        entity_id: int,
        entity_data: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> None:
        """Log entity creation."""
        logger.info(
            "audit.create",
            user_id=user.id,
            user_email=user.email,
            user_role=user.role,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_data=entity_data,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
        )
        AuditLogger._persist(
            db=db,
            action="create",
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=entity_data,
            request_id=request_id,
        )

    @staticmethod
    def log_update(
        db: Session,
        user: User,
        entity_type: str,
        entity_id: int,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> None:
        """Log entity update."""
        # Calculate changes
        changes = {}
        for key, new_value in new_data.items():
            old_value = old_data.get(key)
            if old_value != new_value:
                changes[key] = {"old": old_value, "new": new_value}

        logger.info(
            "audit.update",
            user_id=user.id,
            user_email=user.email,
            user_role=user.role,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
        )
        AuditLogger._persist(
            db=db,
            action="update",
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            payload={"changes": changes},
            request_id=request_id,
        )

    @staticmethod
    def log_delete(
        db: Session,
        user: User,
        entity_type: str,
        entity_id: int,
        entity_data: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> None:
        """Log entity deletion."""
        logger.info(
            "audit.delete",
            user_id=user.id,
            user_email=user.email,
            user_role=user.role,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_data=entity_data,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
        )
        AuditLogger._persist(
            db=db,
            action="delete",
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=entity_data,
            request_id=request_id,
        )

    @staticmethod
    def log_access(
        db: Session,
        user: User,
        entity_type: str,
        entity_id: int,
        action: str = "read",
        request_id: Optional[str] = None,
    ) -> None:
        """Log entity access (for sensitive data)."""
        logger.info(
            "audit.access",
            user_id=user.id,
            user_email=user.email,
            user_role=user.role,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
        )
        AuditLogger._persist(
            db=db,
            action=action,
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=None,
            request_id=request_id,
        )

    @staticmethod
    def log_auth_event(
        email: str,
        event_type: str,  # login_success, login_failed, logout, token_refresh
        ip_address: str,
        user_agent: str,
        success: bool = True,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log authentication events."""
        log_func = logger.info if success else logger.warning
        log_func(
            f"audit.auth.{event_type}",
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            reason=reason,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
        )

    @staticmethod
    def log_permission_denied(
        user: User,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        required_role: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log permission denied events."""
        logger.warning(
            "audit.permission_denied",
            user_id=user.id,
            user_email=user.email,
            user_role=user.role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            required_role=required_role,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
        )
