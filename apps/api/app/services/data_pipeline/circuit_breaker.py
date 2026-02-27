"""Circuit breaker for external data sources.

Redis-backed circuit breaker to prevent cascading failures when external
data sources are down.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum

import redis
import structlog

log = structlog.get_logger()


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, skip requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Redis-backed circuit breaker for external data sources.

    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed

    After N consecutive failures -> OPEN for cooldown period
    After cooldown -> HALF_OPEN, try one request
    On success in HALF_OPEN -> CLOSED
    On failure in HALF_OPEN -> OPEN again
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        provider_name: str,
        failure_threshold: int = 3,
        cooldown_seconds: int = 300,
    ):
        """Initialize circuit breaker.

        Args:
            redis_client: Redis connection
            provider_name: Unique name for this provider
            failure_threshold: Number of failures before opening circuit
            cooldown_seconds: Seconds to wait before attempting recovery
        """
        self.redis = redis_client
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        # Redis keys
        self.state_key = f"circuit_breaker:{provider_name}:state"
        self.failures_key = f"circuit_breaker:{provider_name}:failures"
        self.last_failure_key = f"circuit_breaker:{provider_name}:last_failure"

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        state_str = self.redis.get(self.state_key)
        if not state_str:
            return CircuitState.CLOSED

        # Type assertion: redis.get returns bytes | None
        assert isinstance(state_str, bytes)
        state = CircuitState(state_str.decode("utf-8"))

        # Check if OPEN circuit should transition to HALF_OPEN
        if state == CircuitState.OPEN:
            last_failure_str = self.redis.get(self.last_failure_key)
            if last_failure_str:
                try:
                    assert isinstance(last_failure_str, bytes)
                    last_failure = datetime.fromisoformat(
                        last_failure_str.decode("utf-8")
                    )
                    cooldown_end = last_failure + timedelta(
                        seconds=self.cooldown_seconds
                    )
                    if datetime.now(timezone.utc) >= cooldown_end:
                        # Cooldown expired, try recovery
                        self._set_state(CircuitState.HALF_OPEN)
                        return CircuitState.HALF_OPEN
                except Exception as e:
                    log.warning(
                        "circuit_breaker_cooldown_check_failed",
                        provider=self.provider_name,
                        error=str(e),
                    )

        return state

    def _set_state(self, state: CircuitState) -> None:
        """Set circuit breaker state in Redis."""
        self.redis.set(self.state_key, state.value, ex=86400)  # 24h TTL
        log.info(
            "circuit_breaker_state_change",
            provider=self.provider_name,
            new_state=state.value,
        )

    def can_attempt(self) -> bool:
        """Check if request should be attempted.

        Returns:
            True if request should be attempted, False if circuit is open
        """
        state = self.get_state()
        if state == CircuitState.OPEN:
            log.warning(
                "circuit_breaker_blocked",
                provider=self.provider_name,
                state=state.value,
            )
            return False
        return True

    def record_success(self) -> None:
        """Record successful request."""
        state = self.get_state()

        # Reset failure count
        self.redis.delete(self.failures_key)
        self.redis.delete(self.last_failure_key)

        # If we were in HALF_OPEN, return to CLOSED
        if state == CircuitState.HALF_OPEN:
            self._set_state(CircuitState.CLOSED)

        log.info(
            "circuit_breaker_success",
            provider=self.provider_name,
            state=self.get_state().value,
        )

    def record_failure(self) -> None:
        """Record failed request."""
        state = self.get_state()

        # Increment failure count
        failures_result = self.redis.incr(self.failures_key)
        # Handle potential Awaitable or None return from redis.incr
        if failures_result is None:
            failures_int = 1
        else:
            failures_int = int(failures_result)  # type: ignore[arg-type]
        self.redis.expire(self.failures_key, 3600)  # 1h TTL

        # Record timestamp
        now = datetime.now(timezone.utc).isoformat()
        self.redis.set(self.last_failure_key, now, ex=3600)

        log.warning(
            "circuit_breaker_failure",
            provider=self.provider_name,
            failures=failures_int,
            threshold=self.failure_threshold,
        )

        # Check if we should open the circuit
        if state == CircuitState.HALF_OPEN:
            # Failed during recovery test, go back to OPEN
            self._set_state(CircuitState.OPEN)
        elif failures_int >= self.failure_threshold:
            # Too many failures, open circuit
            self._set_state(CircuitState.OPEN)

    def get_status(self) -> dict:
        """Get circuit breaker status for monitoring.

        Returns:
            Dictionary with state, failures, and last failure time
        """
        state = self.get_state()
        failures_bytes = self.redis.get(self.failures_key)
        failures = (
            int(failures_bytes)
            if failures_bytes and isinstance(failures_bytes, bytes)
            else 0
        )

        last_failure_str = self.redis.get(self.last_failure_key)
        last_failure = None
        if last_failure_str and isinstance(last_failure_str, bytes):
            try:
                last_failure = last_failure_str.decode("utf-8")
            except Exception:
                pass

        return {
            "provider": self.provider_name,
            "state": state.value,
            "failures": failures,
            "failure_threshold": self.failure_threshold,
            "last_failure": last_failure,
            "cooldown_seconds": self.cooldown_seconds,
        }

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self.redis.delete(self.state_key)
        self.redis.delete(self.failures_key)
        self.redis.delete(self.last_failure_key)
        log.info("circuit_breaker_reset", provider=self.provider_name)
