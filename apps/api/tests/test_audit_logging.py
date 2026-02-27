"""Tests for audit logging."""

from app.core.audit import AuditLogger
from app.models.user import User
from app.core.security import hash_password


def test_audit_log_create(db):
    """Test audit logging for create operations."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("password"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    entity_data = {"name": "Test Entity", "value": 100}

    # Should not raise exception
    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=1,
        entity_data=entity_data,
    )


def test_audit_log_update(db):
    """Test audit logging for update operations."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("password"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    old_data = {"name": "Old Name"}
    new_data = {"name": "New Name"}

    # Should not raise exception
    AuditLogger.log_update(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=1,
        old_data=old_data,
        new_data=new_data,
    )


def test_audit_log_delete(db):
    """Test audit logging for delete operations."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("password"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    entity_data = {"name": "Deleted Entity"}

    # Should not raise exception
    AuditLogger.log_delete(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=1,
        entity_data=entity_data,
    )


def test_audit_log_with_request_id(db):
    """Test audit logging with request ID."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("password"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    entity_data = {"name": "Test Entity"}
    request_id = "test-request-123"

    # Should not raise exception
    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=1,
        entity_data=entity_data,
        request_id=request_id,
    )


def test_audit_log_different_entity_types(db):
    """Test audit logging for different entity types."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("password"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    entity_types = ["cooperative", "roaster", "lot", "source"]

    for entity_type in entity_types:
        AuditLogger.log_create(
            db=db,
            user=user,
            entity_type=entity_type,
            entity_id=1,
            entity_data={"test": "data"},
        )


def test_audit_log_analyst_user(db):
    """Test audit logging with analyst user."""
    user = User(
        email="analyst@example.com",
        password_hash=hash_password("password"),
        role="analyst",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=1,
        entity_data={"name": "Test"},
    )


def test_audit_log_complex_entity_data(db):
    """Test audit logging with complex entity data."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("password"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    complex_data = {
        "name": "Test Entity",
        "nested": {"key": "value"},
        "list": [1, 2, 3],
        "bool": True,
        "null": None,
    }

    AuditLogger.log_create(
        db=db,
        user=user,
        entity_type="cooperative",
        entity_id=1,
        entity_data=complex_data,
    )
