"""Security contracts for local and distributed rate limiting."""

from __future__ import annotations

import os
import sys
import threading
from collections import deque

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

import unicorefw
from unicorefw.security import (
    DistributedRateLimiter,
    InputValidationError,
    LocalRateLimiter,
    RateLimitBackend,
    RateLimiter,
    RedisRateLimitBackend,
    SecurityError,
    require_callable,
)


class _Backend(RateLimitBackend):
    def __init__(self, result=True, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def acquire(self, key, max_calls, time_window):
        self.calls.append((key, max_calls, time_window))
        if self.error is not None:
            raise self.error
        return self.result


class _RedisClient:
    def __init__(self, response=1, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def eval(self, *args):
        self.calls.append(args)
        if self.error is not None:
            raise self.error
        return self.response


def test_local_rate_limiter_uses_compatibility_alias_deque_and_window_boundary():
    now = [10.0]
    limiter = LocalRateLimiter(max_calls=2, time_window=5, clock=lambda: now[0])

    assert LocalRateLimiter is RateLimiter
    with limiter:
        pass
    with limiter:
        pass
    assert isinstance(limiter.calls, deque)
    assert list(limiter.calls) == [10.0, 10.0]

    with pytest.raises(SecurityError, match="Rate limit exceeded"), limiter:
        pass

    now[0] = 15.0
    with limiter:
        pass
    assert list(limiter.calls) == [15.0]


def test_rate_limit_contracts_are_available_from_the_package_root():
    assert unicorefw.LocalRateLimiter is LocalRateLimiter
    assert unicorefw.DistributedRateLimiter is DistributedRateLimiter
    assert unicorefw.RedisRateLimitBackend is RedisRateLimitBackend
    assert unicorefw.RateLimitBackend is RateLimitBackend
    assert unicorefw.require_callable is require_callable


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_calls": 0}, "positive integer"),
        ({"max_calls": True}, "positive integer"),
        ({"max_calls": "1"}, "positive integer"),
        ({"max_calls": 1_000_001}, "hard safety maximum"),
        ({"time_window": 0}, "positive"),
        ({"time_window": False}, "finite number"),
        ({"time_window": "1"}, "finite number"),
        ({"time_window": float("inf")}, "finite positive"),
        ({"time_window": 31_536_001}, "hard safety maximum"),
    ],
)
def test_local_rate_limiter_rejects_unbounded_or_invalid_policy(kwargs, message):
    with pytest.raises(InputValidationError, match=message):
        RateLimiter(**kwargs)


def test_local_rate_limiter_rejects_invalid_clock_and_clock_results():
    with pytest.raises(InputValidationError, match="clock must be callable"):
        RateLimiter(clock=object())  # type: ignore[arg-type]

    for invalid in (True, "1", float("inf"), float("nan")):
        limiter = RateLimiter(clock=lambda value=invalid: value) # type: ignore
        with pytest.raises(SecurityError, match="finite number"), limiter:
            pass


def test_local_rate_limiter_fails_closed_if_clock_moves_backwards():
    values = iter((2.0, 1.0))
    limiter = RateLimiter(clock=lambda: next(values))

    with limiter:
        pass
    with pytest.raises(SecurityError, match="moved backwards"), limiter:
        pass


def test_local_rate_limiter_serializes_concurrent_admission():
    limiter = RateLimiter(max_calls=4, clock=lambda: 10.0)
    barrier = threading.Barrier(12)
    admitted = []
    rejected = []

    def attempt():
        barrier.wait()
        try:
            with limiter:
                admitted.append(True)
        except SecurityError:
            rejected.append(True)

    threads = [threading.Thread(target=attempt) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)

    assert all(not thread.is_alive() for thread in threads)
    assert len(admitted) == 4
    assert len(rejected) == 8


def test_rate_limit_backend_documents_required_atomic_method():
    with pytest.raises(NotImplementedError):
        RateLimitBackend().acquire("client", 1, 1.0)


def test_distributed_rate_limiter_admits_and_passes_validated_policy():
    backend = _Backend()
    limiter = DistributedRateLimiter(backend, "client:42", 2, 1.5)

    with limiter:
        pass

    assert backend.calls == [("client:42", 2, 1.5)]


def test_distributed_rate_limiter_rejects_denial_invalid_response_and_failure():
    with pytest.raises(SecurityError, match="Rate limit exceeded"), DistributedRateLimiter(_Backend(result=False), "client"):
        pass

    with pytest.raises(SecurityError, match="invalid response"), DistributedRateLimiter(_Backend(result=1), "client"): # type: ignore
        pass

    failure = RuntimeError("redis://user:secret@example.invalid")
    with pytest.raises(SecurityError, match="backend failed") as caught, DistributedRateLimiter(_Backend(error=failure), "client"):
        pass
    assert "secret" not in str(caught.value)
    assert caught.value.__cause__ is failure


@pytest.mark.parametrize("key", ["", " ", "client\nforged", "x" * 513])
def test_distributed_rate_limiter_rejects_invalid_keys(key):
    with pytest.raises(InputValidationError):
        DistributedRateLimiter(_Backend(), key)


def test_distributed_rate_limiter_requires_backend_protocol():
    with pytest.raises(InputValidationError, match="callable acquire"):
        DistributedRateLimiter(object(), "client")  # type: ignore[arg-type]


def test_redis_backend_uses_one_atomic_eval_and_hashes_client_key():
    client = _RedisClient(response=1)
    backend = RedisRateLimitBackend(client, namespace="test:rate")

    assert backend.acquire("customer@example.com", 3, 1.001)
    script, key_count, redis_key, max_calls, window_ms, member = client.calls[0]
    assert script == RedisRateLimitBackend._SCRIPT
    assert key_count == 1
    assert redis_key.startswith("test:rate:")
    assert "customer@example.com" not in redis_key
    assert max_calls == 3
    assert window_ms == 1001
    assert len(member) == 32


def test_redis_backend_returns_denial_and_rejects_invalid_response():
    assert not RedisRateLimitBackend(_RedisClient(response=0)).acquire(
        "client",
        1,
        1,
    )

    with pytest.raises(SecurityError, match="invalid response"):
        RedisRateLimitBackend(_RedisClient(response=None)).acquire("client", 1, 1) # type: ignore


def test_redis_backend_redacts_client_failure_and_validates_direct_calls():
    failure = RuntimeError("redis://user:secret@example.invalid")
    with pytest.raises(SecurityError, match="Redis rate limit backend failed") as caught:
        RedisRateLimitBackend(_RedisClient(error=failure)).acquire("client", 1, 1)
    assert "secret" not in str(caught.value)
    assert caught.value.__cause__ is failure

    backend = RedisRateLimitBackend(_RedisClient())
    with pytest.raises(InputValidationError, match="control characters"):
        backend.acquire("client\x00secret", 1, 1)
    with pytest.raises(InputValidationError, match="positive integer"):
        backend.acquire("client", 0, 1)


@pytest.mark.parametrize(
    ("client", "namespace"),
    [
        (object(), "valid"),
        (_RedisClient(), ""),
        (_RedisClient(), "x" * 129),
        (_RedisClient(), "test\nforged"),
    ],
)
def test_redis_backend_rejects_invalid_configuration(client, namespace):
    with pytest.raises(InputValidationError):
        RedisRateLimitBackend(client, namespace=namespace)


def test_require_callable_makes_only_a_callability_claim():
    callback = lambda: None
    assert require_callable(callback, "callback") is callback
    with pytest.raises(InputValidationError, match="callback must be callable"):
        require_callable("callback", "callback")
