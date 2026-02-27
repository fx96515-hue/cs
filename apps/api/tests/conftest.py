import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault(
    "JWT_SECRET",
    "test_jwt_secret_key_for_testing_only_must_be_at_least_32_chars",
)
os.environ.setdefault("JWT_ISSUER", "coffeestudio-test")
os.environ.setdefault("JWT_AUDIENCE", "coffeestudio-test")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "TestAdminP@ss123!")
os.environ.setdefault("GRAPH_ENABLED", "true")
os.environ.setdefault("SENTIMENT_ENABLED", "true")
os.environ.setdefault("REALTIME_PRICE_FEED_ENABLED", "true")
os.environ.setdefault("ANOMALY_DETECTION_ENABLED", "true")
os.environ.setdefault("SEMANTIC_SEARCH_ENABLED", "true")
os.environ.setdefault("ASSISTANT_ENABLED", "true")


# Import after env vars are set
from app.db.session import get_db, Base
from app.main import app
from app.models.user import User
from app.core.security import hash_password, create_access_token

# Test database setup with in-memory SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Automatically set timestamps for all models with created_at/updated_at
@event.listens_for(Base, "before_insert", propagate=True)
def receive_before_insert(mapper, connection, target):
    """Set created_at and updated_at before insert for SQLite compatibility."""
    now = datetime.now(timezone.utc)
    if hasattr(target, "created_at") and target.created_at is None:
        target.created_at = now
    if hasattr(target, "updated_at") and target.updated_at is None:
        target.updated_at = now


@event.listens_for(Base, "before_update", propagate=True)
def receive_before_update(mapper, connection, target):
    """Update updated_at before update for SQLite compatibility."""
    if hasattr(target, "updated_at"):
        target.updated_at = datetime.now(timezone.utc)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test.

    Note: For SQLite compatibility, we remove server_default from timestamp columns
    and set timestamps via SQLAlchemy events (see above).
    """
    # Invalidate knowledge graph cache so each test builds a fresh graph
    from app.services import knowledge_graph as kg_service

    kg_service.invalidate_cache()

    # Remove server_default from timestamp columns for SQLite compatibility
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.name in ("created_at", "updated_at"):
                column.server_default = None

    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with overridden database dependency."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Reset rate limiter state before each test
    if hasattr(app.state, "limiter"):
        # Clear the app-level rate limiter's storage
        try:
            app.state.limiter._storage.storage.clear()
        except AttributeError:
            pass

    # Also clear the auth-module rate limiter to prevent cross-test contamination
    try:
        from app.api.routes import auth as auth_module

        if hasattr(auth_module, "limiter"):
            _s = auth_module.limiter._storage
            if hasattr(_s, "storage"):
                _s.storage.clear()
            elif hasattr(_s, "reset"):
                _s.reset()
    except (ImportError, AttributeError):
        pass

    yield TestClient(app)

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create a test user for authentication."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestP@ss123!"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_analyst_user(db):
    """Create a test analyst user."""
    user = User(
        email="analyst@example.com",
        password_hash=hash_password("AnalystP@ss123!"),
        role="analyst",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_viewer_user(db):
    """Create a test viewer user."""
    user = User(
        email="viewer@example.com",
        password_hash=hash_password("ViewerP@ss123!"),
        role="viewer",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create JWT token headers for test user."""
    token = create_access_token(sub=test_user.email, role=test_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst_auth_headers(test_analyst_user):
    """Create JWT token headers for analyst user."""
    token = create_access_token(
        sub=test_analyst_user.email, role=test_analyst_user.role
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_auth_headers(test_viewer_user):
    """Create JWT token headers for viewer user."""
    token = create_access_token(sub=test_viewer_user.email, role=test_viewer_user.role)
    return {"Authorization": f"Bearer {token}"}
