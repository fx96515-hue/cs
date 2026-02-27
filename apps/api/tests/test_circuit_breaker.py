"""Tests for circuit breaker."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.services.data_pipeline.circuit_breaker import CircuitBreaker, CircuitState


def test_circuit_breaker_initial_state():
    """Test circuit breaker starts in CLOSED state."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None

    breaker = CircuitBreaker(mock_redis, "test_provider")
    state = breaker.get_state()

    assert state == CircuitState.CLOSED


def test_circuit_breaker_allows_requests_when_closed():
    """Test circuit breaker allows requests when closed."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None

    breaker = CircuitBreaker(mock_redis, "test_provider")

    assert breaker.can_attempt() is True


def test_circuit_breaker_blocks_requests_when_open():
    """Test circuit breaker blocks requests when open."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = b"open"

    breaker = CircuitBreaker(mock_redis, "test_provider")

    assert breaker.can_attempt() is False


def test_circuit_breaker_opens_after_threshold_failures():
    """Test circuit breaker opens after reaching failure threshold."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.incr.side_effect = [1, 2, 3]  # Simulate failure count

    breaker = CircuitBreaker(
        mock_redis, "test_provider", failure_threshold=3, cooldown_seconds=300
    )

    # First two failures don't open circuit
    breaker.record_failure()
    breaker.record_failure()

    # Third failure should open circuit
    breaker.record_failure()

    # Verify state was set to OPEN
    assert mock_redis.set.called


def test_circuit_breaker_resets_on_success():
    """Test circuit breaker resets failure count on success."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None

    breaker = CircuitBreaker(mock_redis, "test_provider")
    breaker.record_success()

    # Should delete failure-related keys
    assert mock_redis.delete.call_count >= 2


def test_circuit_breaker_transitions_to_half_open():
    """Test circuit breaker transitions from OPEN to HALF_OPEN after cooldown."""
    mock_redis = MagicMock()

    # Circuit is OPEN
    mock_redis.get.side_effect = [
        b"open",  # state key
        (datetime.now(timezone.utc) - timedelta(seconds=400))
        .isoformat()
        .encode(),  # last failure (expired)
    ]

    breaker = CircuitBreaker(
        mock_redis, "test_provider", failure_threshold=3, cooldown_seconds=300
    )

    state = breaker.get_state()

    # Should transition to HALF_OPEN
    assert state == CircuitState.HALF_OPEN


def test_circuit_breaker_stays_open_during_cooldown():
    """Test circuit breaker stays OPEN during cooldown period."""
    mock_redis = MagicMock()

    # Circuit is OPEN, recent failure
    mock_redis.get.side_effect = [
        b"open",  # state key
        datetime.now(timezone.utc).isoformat().encode(),  # last failure (recent)
    ]

    breaker = CircuitBreaker(
        mock_redis, "test_provider", failure_threshold=3, cooldown_seconds=300
    )

    state = breaker.get_state()

    assert state == CircuitState.OPEN


def test_circuit_breaker_closes_from_half_open_on_success():
    """Test circuit breaker closes from HALF_OPEN on successful request."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = b"half_open"

    breaker = CircuitBreaker(mock_redis, "test_provider")
    breaker.record_success()

    # Should set state to CLOSED
    assert mock_redis.set.called


def test_circuit_breaker_reopens_from_half_open_on_failure():
    """Test circuit breaker reopens from HALF_OPEN on failed request."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = b"half_open"
    mock_redis.incr.return_value = 1

    breaker = CircuitBreaker(mock_redis, "test_provider")
    breaker.record_failure()

    # Should set state back to OPEN
    assert mock_redis.set.called


def test_circuit_breaker_get_status():
    """Test getting circuit breaker status."""
    mock_redis = MagicMock()
    mock_redis.get.side_effect = [
        b"closed",  # state
        b"2",  # failures
        b"2024-01-01T12:00:00+00:00",  # last failure
    ]

    breaker = CircuitBreaker(mock_redis, "test_provider", failure_threshold=3)
    status = breaker.get_status()

    assert status["provider"] == "test_provider"
    assert status["state"] == "closed"
    assert status["failures"] == 2
    assert status["failure_threshold"] == 3
    assert "last_failure" in status


def test_circuit_breaker_reset():
    """Test resetting circuit breaker."""
    mock_redis = MagicMock()

    breaker = CircuitBreaker(mock_redis, "test_provider")
    breaker.reset()

    # Should delete all keys
    assert mock_redis.delete.call_count >= 3
