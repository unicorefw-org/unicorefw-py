"""Opt-in integration tests for the atomic Redis rate-limit backend."""

from __future__ import annotations

import hashlib
import os
import secrets
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw.security import RedisRateLimitBackend

pytestmark = pytest.mark.redis_integration


def _redis_client():
    if os.environ.get("UNICORE_FW_REDIS_INTEGRATION") != "1":
        pytest.skip("Redis integration is not enabled")

    host = os.environ.get("UNICORE_FW_REDIS_HOST", "127.0.0.1")
    port_text = os.environ.get("UNICORE_FW_REDIS_PORT", "6379")
    if host != "127.0.0.1" or port_text != "6379":
        pytest.fail(
            "Redis integration requires the dedicated 127.0.0.1:6379 service"
        )

    redis = pytest.importorskip("redis")
    client = redis.Redis(
        host=host,
        port=6379,
        db=15,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    client.ping()
    return client


def test_redis_backend_enforces_atomic_concurrent_limit_and_expiry():
    client = _redis_client()
    namespace = f"unicorefw:test:{secrets.token_hex(8)}"
    backend = RedisRateLimitBackend(client, namespace=namespace)
    client_identifier = "authenticated-client"
    expiry_identifier = "expiry-client"
    redis_key = (
        f"{namespace}:"
        f"{hashlib.sha256(client_identifier.encode('utf-8')).hexdigest()}"
    )
    expiry_redis_key = (
        f"{namespace}:"
        f"{hashlib.sha256(expiry_identifier.encode('utf-8')).hexdigest()}"
    )

    try:
        with ThreadPoolExecutor(max_workers=16) as executor:
            admissions = list(
                executor.map(
                    lambda _: backend.acquire(client_identifier, 5, 10),
                    range(32),
                )
            )

        assert admissions.count(True) == 5
        assert admissions.count(False) == 27
        assert client.zcard(redis_key) == 5
        assert 0 < client.pttl(redis_key) <= 10_000
        assert not list(
            client.scan_iter(match=f"{namespace}:*{client_identifier}*")
        )

        assert backend.acquire(expiry_identifier, 1, 0.1)
        assert not backend.acquire(expiry_identifier, 1, 0.1)
        # The backend itself never relies on the application host clock.
        time.sleep(0.2)
        assert backend.acquire(expiry_identifier, 1, 0.1)
    finally:
        client.delete(redis_key, expiry_redis_key)
        client.close()
