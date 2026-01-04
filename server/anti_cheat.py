import time
from dataclasses import dataclass

from server.metrics import Metrics


@dataclass
class RateLimiter:
    capacity: int
    refill_per_second: int
    tokens: float = 0
    last_refill: float = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class AntiCheat:
    """
    Lightweight anti-cheat utilities for the sample server.
    """

    def __init__(self, metrics: Metrics, rate_limit_per_second: int, max_message_size: int):
        self.metrics = metrics
        self.rate_limit_per_second = rate_limit_per_second
        self.max_message_size = max_message_size
        self._limiters = {}

    def validate_password(self, supplied: str, expected: str | None) -> bool:
        if expected is None:
            return True
        return supplied == expected

    def validate_message_size(self, message: bytes) -> bool:
        ok = len(message) <= self.max_message_size
        if not ok:
            self.metrics.increment("messages_rejected_size")
        return ok

    def allow_message(self, client_id: str) -> bool:
        limiter = self._limiters.setdefault(
            client_id,
            RateLimiter(capacity=self.rate_limit_per_second, refill_per_second=self.rate_limit_per_second),
        )
        allowed = limiter.allow()
        if not allowed:
            self.metrics.increment("messages_rejected_rate")
        return allowed
