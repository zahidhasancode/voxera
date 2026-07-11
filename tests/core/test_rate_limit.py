"""Rate limit middleware tests."""

from app.core.rate_limit import _SlidingWindowCounter


def test_sliding_window_allows_under_limit():
    counter = _SlidingWindowCounter(limit=3, window_seconds=60)
    assert counter.allow("client")[0] is True
    assert counter.allow("client")[0] is True
    assert counter.allow("client")[0] is True


def test_sliding_window_blocks_over_limit():
    counter = _SlidingWindowCounter(limit=2, window_seconds=60)
    counter.allow("client")
    counter.allow("client")
    allowed, retry_after = counter.allow("client")
    assert allowed is False
    assert retry_after is not None
