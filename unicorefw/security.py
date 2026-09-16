"""
File: unicorefw/security.py
Security utilities for UniCoreFW.

This module contains classes and functions for security-related operations
like input validation, sanitization, and rate limiting.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""

import hashlib as _hashlib
import json
import logging
import math
import os
import secrets as _secrets
import stat
import sys
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from typing_extensions import Self


class SecurityError(Exception):
    """Base exception for security-related errors."""

class InputValidationError(SecurityError):
    """Raised when input validation fails."""

class AuthorizationError(SecurityError):
    """Raised when authorization checks fail."""

class SanitizationError(SecurityError):
    """Raised when data sanitization fails."""


class ResourceLimitError(SecurityError):
    """Raised before caller-controlled work exceeds a configured resource budget."""

    def __init__(
        self,
        resource: str,
        limit: float,
        observed: float | None = None,
    ):
        self.resource = resource
        self.limit = limit
        self.observed = observed
        message = f"{resource} exceeds the configured limit of {limit}"
        if observed is not None:
            message += f" (observed {observed})"
        super().__init__(message)


def _validate_resource_limit(value: Any, name: str, hard_maximum: int) -> int:
    """Validate one positive integer limit against a library safety ceiling."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InputValidationError(f"{name} must be a positive integer")
    if value > hard_maximum:
        raise InputValidationError(
            f"{name} cannot exceed the hard safety maximum of {hard_maximum}"
        )
    return value


def _validate_resource_ratio(
    value: Any,
    name: str,
    hard_maximum: float,
) -> float:
    """Validate one ratio limit against a library safety ceiling."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputValidationError(
            f"{name} must be a number greater than or equal to 1"
        )
    numeric_value = float(value)
    if not math.isfinite(numeric_value) or numeric_value < 1:
        raise InputValidationError(
            f"{name} must be a finite number greater than or equal to 1"
        )
    if numeric_value > hard_maximum:
        raise InputValidationError(
            f"{name} cannot exceed the hard safety maximum of {hard_maximum:g}"
        )
    return numeric_value


def _validate_resource_duration(
    value: Any,
    name: str,
    hard_maximum: float,
    *,
    allow_zero: bool = False,
) -> float:
    """Validate a finite duration against a library safety ceiling."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputValidationError(f"{name} must be a finite number")
    numeric_value = float(value)
    minimum = 0 if allow_zero else 0.0
    if not math.isfinite(numeric_value) or (
        numeric_value < minimum if allow_zero else numeric_value <= minimum
    ):
        qualifier = "non-negative" if allow_zero else "positive"
        raise InputValidationError(f"{name} must be a finite {qualifier} number")
    if numeric_value > hard_maximum:
        raise InputValidationError(
            f"{name} cannot exceed the hard safety maximum of {hard_maximum:g}"
        )
    return numeric_value


def _estimate_resource_weight(value: Any, limit: int) -> int:
    """Estimate built-in container weight and stop after crossing ``limit``."""
    total = 0
    pending = [value]
    seen = set()
    container_types = (dict, list, tuple, set, frozenset, deque)

    while pending:
        current = pending.pop()
        if isinstance(current, container_types):
            identity = id(current)
            if identity in seen:
                continue
            seen.add(identity)

        total += sys.getsizeof(current)
        if total > limit:
            return total

        if isinstance(current, dict):
            pending.extend(current.keys())
            pending.extend(current.values())
        elif isinstance(current, (list, tuple, set, frozenset, deque)):
            pending.extend(current)

    return total


_MAX_RATE_LIMIT_CALLS = 1_000_000
_MAX_RATE_LIMIT_WINDOW_SECONDS = 31_536_000.0
_MAX_RATE_LIMIT_KEY_LENGTH = 512
_MAX_RATE_LIMIT_NAMESPACE_LENGTH = 128


def _validate_rate_limit_policy(
    max_calls: Any,
    time_window: Any,
) -> tuple[int, float]:
    """Validate a rate-limit policy against bounded library ceilings."""
    return (
        _validate_resource_limit(
            max_calls,
            "max_calls",
            _MAX_RATE_LIMIT_CALLS,
        ),
        _validate_resource_duration(
            time_window,
            "time_window",
            _MAX_RATE_LIMIT_WINDOW_SECONDS,
        ),
    )


def _validate_rate_limit_identifier(value: Any, name: str, max_length: int) -> str:
    """Validate a non-empty, bounded identifier without echoing it in errors."""
    if not isinstance(value, str) or not value.strip():
        raise InputValidationError(f"{name} must be non-empty text")
    if len(value) > max_length:
        raise InputValidationError(f"{name} cannot exceed {max_length} characters")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise InputValidationError(f"{name} cannot contain control characters")
    return value


class RateLimiter:
    """
    Thread-safe, process-local rate limiter.

    This class provides a context manager interface for rate limiting operations.
    It prevents more than `max_calls` operations within `time_window` seconds.
    State is not shared between processes or hosts, so this class must not be
    used as a distributed abuse-control boundary. Use `DistributedRateLimiter`
    with an atomic shared backend for that purpose.
    """

    def __init__(
        self,
        max_calls: int = 100,
        time_window: float = 60,
        *,
        clock: Callable[[], float] = time.monotonic,
    ):
        """
        Initialize a RateLimiter.

        Args:
            max_calls: Maximum number of calls allowed in the time window
            time_window: Time window in seconds
            clock: Monotonic clock dependency. Intended for deterministic tests;
                production callers should use the secure default.
        """
        self.max_calls, self.time_window = _validate_rate_limit_policy(
            max_calls,
            time_window,
        )
        if not callable(clock):
            raise InputValidationError("clock must be callable")
        self.calls = deque()
        self._clock = clock
        self._last_time: float | None = None
        self._lock = threading.Lock()

    def __enter__(self):
        """
        Enter the context manager, checking if the rate limit has been exceeded.

        Raises:
            SecurityError: If the rate limit is exceeded
        """
        with self._lock:
            clock_value = self._clock()
            if (
                isinstance(clock_value, bool)
                or not isinstance(clock_value, (int, float))
                or not math.isfinite(float(clock_value))
            ):
                raise SecurityError("Rate limiter clock must return a finite number")
            now = float(clock_value)
            if self._last_time is not None and now < self._last_time:
                raise SecurityError("Rate limiter clock moved backwards")
            self._last_time = now

            cutoff = now - self.time_window
            while self.calls and self.calls[0] <= cutoff:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                raise SecurityError("Rate limit exceeded")

            self.calls.append(now)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""


LocalRateLimiter = RateLimiter


class RateLimitBackend:
    """
    Structural contract for atomic distributed rate-limit backends.

    Implementations must perform expiry, count, and admission as one atomic
    operation and return `True` only when the request is admitted.
    """

    def acquire(
        self,
        key: str,
        max_calls: int,
        time_window: float,
    ) -> bool:
        """Atomically admit or reject one request."""
        raise NotImplementedError


class DistributedRateLimiter:
    """Context manager backed by an atomic shared rate-limit implementation."""

    def __init__(
        self,
        backend: RateLimitBackend,
        key: str,
        max_calls: int = 100,
        time_window: float = 60,
    ):
        acquire = getattr(backend, "acquire", None)
        if not callable(acquire):
            raise InputValidationError("backend must provide a callable acquire method")
        self.backend = backend
        self.key = _validate_rate_limit_identifier(
            key,
            "key",
            _MAX_RATE_LIMIT_KEY_LENGTH,
        )
        self.max_calls, self.time_window = _validate_rate_limit_policy(
            max_calls,
            time_window,
        )

    def __enter__(self):
        """Atomically consume one distributed rate-limit allowance."""
        try:
            admitted = self.backend.acquire(
                self.key,
                self.max_calls,
                self.time_window,
            )
        except Exception as exc:
            raise SecurityError("Distributed rate limit backend failed") from exc
        if not isinstance(admitted, bool):
            raise SecurityError(
                "Distributed rate limit backend returned an invalid response"
            )
        if not admitted:
            raise SecurityError("Rate limit exceeded")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""


class RedisRateLimitBackend(RateLimitBackend):
    """
    Atomic Redis sorted-set backend for `DistributedRateLimiter`.

    The injected client must provide the standard redis-py `eval` method. Client
    identifiers are SHA-256 hashed before they are placed in Redis keys.
    """

    _SCRIPT = """
local current_time = redis.call('TIME')
local now_ms = (current_time[1] * 1000) + math.floor(current_time[2] / 1000)
local window_ms = tonumber(ARGV[2])
local cutoff_ms = now_ms - window_ms
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', cutoff_ms)
local count = redis.call('ZCARD', KEYS[1])
if count >= tonumber(ARGV[1]) then
    return 0
end
redis.call('ZADD', KEYS[1], now_ms, ARGV[3])
redis.call('PEXPIRE', KEYS[1], window_ms)
return 1
""".strip()

    def __init__(
        self,
        client: Any,
        namespace: str = "unicorefw:rate-limit",
    ):
        if not callable(getattr(client, "eval", None)):
            raise InputValidationError("client must provide a callable eval method")
        self.client = client
        self.namespace = _validate_rate_limit_identifier(
            namespace,
            "namespace",
            _MAX_RATE_LIMIT_NAMESPACE_LENGTH,
        )

    def acquire(
        self,
        key: str,
        max_calls: int,
        time_window: float,
    ) -> bool:
        """Atomically admit one request using Redis server time."""
        validated_key = _validate_rate_limit_identifier(
            key,
            "key",
            _MAX_RATE_LIMIT_KEY_LENGTH,
        )
        validated_calls, validated_window = _validate_rate_limit_policy(
            max_calls,
            time_window,
        )
        window_ms = math.ceil(validated_window * 1000)
        key_digest = _hashlib.sha256(validated_key.encode("utf-8")).hexdigest()
        redis_key = f"{self.namespace}:{key_digest}"
        member = _secrets.token_hex(16)

        try:
            response = self.client.eval(
                self._SCRIPT,
                1,
                redis_key,
                validated_calls,
                window_ms,
                member,
            )
        except Exception as exc:
            raise SecurityError("Redis rate limit backend failed") from exc
        if response == 1:
            return True
        if response == 0:
            return False
        raise SecurityError("Redis rate limit backend returned an invalid response")


class _SecureAppendFileHandler(logging.Handler):
    """Append UTF-8 log records without following symbolic links."""

    terminator = "\n"

    def __init__(self, log_file: str):
        super().__init__(level=logging.INFO)
        self.log_file = os.path.abspath(os.fspath(log_file))
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        encoded_record = (self.format(record) + self.terminator).encode("utf-8")
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW  # pyright: ignore[reportAttributeAccessIssue]

        descriptor = -1
        try:
            descriptor = os.open(self.log_file, flags, 0o600)
            file_status = os.fstat(descriptor)
            if not stat.S_ISREG(file_status.st_mode):
                raise SecurityError("Audit log destination must be a regular file")
            if hasattr(os, "fchmod"):
                os.fchmod( # type: ignore
                    descriptor, 0o600
                )  # pyright: ignore[reportAttributeAccessIssue]

            remaining = memoryview(encoded_record)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise OSError("Audit log write made no progress")
                remaining = remaining[written:]
        except OSError as exc:
            raise SecurityError("Unable to append the audit event securely") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)


class AuditLogger:
    """
    Secure audit logging implementation.

    This class provides a thread-safe way to log security-related events.
    """

    def __init__(
        self,
        log_file: str = "unicore_audit.log",
        logger: logging.Logger | None = None,
    ):
        """
        Initialize an AuditLogger.

        Args:
            log_file: Path to the log file
            logger: Existing standard-library logger. When supplied, it owns
                routing and log_file is not used.
        """
        self._lock = threading.Lock()
        self._owned_handler: _SecureAppendFileHandler | None = None

        if logger is not None:
            if not isinstance(logger, logging.Logger):
                raise InputValidationError("logger must be a logging.Logger")
            self._logger = logger
            self.log_file = None
            return

        self.log_file = os.path.abspath(os.fspath(log_file))
        self._logger = logging.getLogger(f"unicorefw.audit.{id(self)}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        self._owned_handler = _SecureAppendFileHandler(self.log_file)
        self._logger.addHandler(self._owned_handler)

    def log(self, event_type: str, details: Any) -> None:
        """
        Securely log an event with timestamp and details.

        Args:
            event_type: Type of event (e.g., "LOGIN", "ACCESS_DENIED")
            details: JSON-serializable event details. Other values are rendered
                with their string representation.
        """
        if not isinstance(event_type, str) or not event_type.strip():
            raise InputValidationError("event_type must be non-empty text")
        if "\x00" in event_type:
            raise InputValidationError("event_type cannot contain null bytes")

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details,
            "message": f"{event_type}: {details}",
        }
        serialized_event = json.dumps(
            event,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        with self._lock:
            self._logger.info(
                serialized_event,
                extra={"audit_event": event},
            )

    def close(self) -> None:
        """Detach and close the internally owned file handler."""
        with self._lock:
            if self._owned_handler is None:
                return
            self._logger.removeHandler(self._owned_handler)
            self._owned_handler.close()
            self._owned_handler = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def validate_type(
    value: Any,
    expected_types: type | tuple[type, ...],
    param_name: str = "parameter",
) -> Any:
    """
    Validate that a value matches expected types.

    Args:
        value: The value to validate
        expected_types: Type or tuple of types to check against
        param_name: Name of the parameter for error messages

    Returns:
        The validated value

    Raises:
        InputValidationError: If validation fails
    """
    if not isinstance(value, expected_types):
        raise InputValidationError(
            f"Invalid type for {param_name}. Expected {expected_types}, got {type(value)}"
        )
    return value


def require_callable(func: Any, param_name: str = "parameter") -> Callable:
    """
    Require that a parameter implements Python's callable protocol.

    This check does not establish that the callable is trusted, safe, pure, or
    suitable to run with the caller's privileges. Only accept callables from a
    trusted source when execution has security consequences.

    Args:
        func: The function to validate
        param_name: Name of the parameter for error messages

    Returns:
        The validated function

    Raises:
        InputValidationError: If validation fails
    """
    if not callable(func):
        raise InputValidationError(f"{param_name} must be callable")

    return func


def validate_callable(func: Any, param_name: str = "parameter") -> Callable:
    """
    Backward-compatible alias for `require_callable`.

    The function verifies callability only; it makes no safety or trust claim.
    """
    return require_callable(func, param_name)


def sanitize_string(
    value: Any, max_length: int | None = None, allowed_chars: str | None = None
) -> str:
    """
    Sanitize a string input.

    Args:
        value: String to sanitize
        max_length: Optional maximum length
        allowed_chars: Optional regex pattern of allowed characters

    Returns:
        Sanitized string

    Raises:
        SanitizationError: If sanitization fails
    """
    if not isinstance(value, str):
        raise SanitizationError("Value must be a string")

    # Trim whitespace
    value = value.strip()

    # Check length
    if max_length and len(value) > max_length:
        raise SanitizationError(f"String exceeds maximum length of {max_length}")

    # Check allowed characters
    if allowed_chars:
        import re

        if not re.match(f"^[{allowed_chars}]*$", value):
            raise SanitizationError("String contains invalid characters")

    return value
