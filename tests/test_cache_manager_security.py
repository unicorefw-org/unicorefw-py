"""Security and stability contracts for database query-cache keys."""

from __future__ import annotations

import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw.db import CacheManager
from unicorefw.security import InputValidationError


class _Database:
    def __init__(self):
        self.calls = []

    def fetch_all(self, query, params=None):
        self.calls.append((query, params))
        return [{"query": query, "params": params}]


def test_cache_key_is_length_framed_sha256_and_deterministic():
    cache = CacheManager(_Database()) # type: ignore
    query = "SELECT * FROM items WHERE id = ?"
    params = (7,)
    query_bytes = query.encode("utf-8")
    params_bytes = repr(params).encode("utf-8")
    expected_payload = (
        len(query_bytes).to_bytes(8, "big")
        + query_bytes
        + len(params_bytes).to_bytes(8, "big")
        + params_bytes
    )

    assert cache._cache_key(query, params) == hashlib.sha256(
        expected_payload
    ).hexdigest()
    assert cache._cache_key(query, params) == cache._cache_key(query, params)
    assert cache._cache_key("ab", ("c",)) != cache._cache_key("a", ("bc",))


def test_cache_key_rejects_non_text_query():
    cache = CacheManager(_Database()) # type: ignore

    with pytest.raises(InputValidationError, match="query must be text"):
        cache._cache_key(b"SELECT 1")  # type: ignore[arg-type]


def test_cache_fetch_keeps_parameter_sets_isolated():
    database = _Database()
    cache = CacheManager(database) # type: ignore

    first = cache.fetch_with_cache("SELECT ?", ("first",))
    second = cache.fetch_with_cache("SELECT ?", ("second",))

    assert first != second
    assert database.calls == [
        ("SELECT ?", ("first",)),
        ("SELECT ?", ("second",)),
    ]
    assert cache.fetch_with_cache("SELECT ?", ("first",)) == first
    assert len(database.calls) == 2


def test_cache_set_prunes_expired_keys_before_new_admission():
    current_time = [0.0]
    cache = CacheManager(
        _Database(), # type: ignore
        ttl=1,
        clock=lambda: current_time[0],
    )
    cache.set("SELECT ?", [{"value": "expired"}], ("old",))

    current_time[0] = 1.0
    cache.set("SELECT ?", [{"value": "current"}], ("new",))

    assert cache.get("SELECT ?", ("old",)) is None
    assert cache.get("SELECT ?", ("new",)) == [{"value": "current"}]
    assert cache.cache_info()["entries"] == 1
