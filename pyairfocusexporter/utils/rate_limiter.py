import time
from typing import Optional


class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.last_refill = time.time()

    def acquire(self, tokens: int = 1) -> None:
        self._refill()
        while self.tokens < tokens:
            time.sleep(0.1)
            self._refill()
        self.tokens -= tokens

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def get_available_tokens(self) -> float:
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        return min(self.capacity, self.tokens + new_tokens)


class HeaderBasedRateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 600,
        window_seconds: int = 60,
    ):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self._requests: list[float] = []
        self._rate_limit_remaining: Optional[int] = None
        self._rate_limit_reset: Optional[float] = None

    def acquire(self, tokens: int = 1) -> None:
        now = time.time()
        self._requests = [t for t in self._requests if now - t < self.window_seconds]

        while len(self._requests) >= self.requests_per_minute:
            if self._rate_limit_reset:
                wait_time = self._rate_limit_reset - now
                if wait_time > 0:
                    time.sleep(wait_time)
            else:
                time.sleep(1)
            now = time.time()
            self._requests = [t for t in self._requests if now - t < self.window_seconds]

        self._requests.append(now)

    def update_from_headers(self, remaining: Optional[int], reset: Optional[float]) -> None:
        self._rate_limit_remaining = remaining
        self._rate_limit_reset = reset
