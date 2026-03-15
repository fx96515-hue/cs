"""
pytest configuration for coverage reporting.
Run: pytest --cov=apps/api/app --cov-report=html apps/api/tests
"""

import pytest


def pytest_configure(config):
    """Configure pytest with coverage markers."""
    config.addinivalue_line("markers", "coverage: coverage-related tests")


@pytest.fixture(scope="session")
def cov_threshold():
    """Define minimum coverage thresholds by module."""
    return {
        "core": 90,  # Critical auth/config
        "models": 85,  # ORM models
        "schemas": 80,  # Validation
        "services": 85,  # Business logic
        "api": 80,  # Endpoints
        "ml": 75,  # ML models
        "workers": 70,  # Async tasks
    }
