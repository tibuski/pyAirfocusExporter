import pytest
from pyairfocusexporter.utils.rate_limiter import TokenBucketRateLimiter, HeaderBasedRateLimiter


def test_token_bucket_rate_limiter() -> None:
    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)
    limiter.acquire(1)
    assert limiter.tokens < 10


def test_header_based_rate_limiter_creation() -> None:
    limiter = HeaderBasedRateLimiter(requests_per_minute=600, window_seconds=60)
    assert limiter.requests_per_minute == 600
    assert limiter.window_seconds == 60
