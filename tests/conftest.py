import os

# Provide minimal defaults for unit tests that import app settings directly.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault(
    "JWT_SECRET",
    "test_jwt_secret_key_for_testing_only_must_be_at_least_32_chars",
)
os.environ.setdefault("JWT_ISSUER", "coffeestudio-test")
os.environ.setdefault("JWT_AUDIENCE", "coffeestudio-test")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", "admin@coffeestudio.com")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "AdminAdmin123!")
