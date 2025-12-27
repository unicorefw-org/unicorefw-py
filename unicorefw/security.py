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

import threading
import time
from typing import Any, Callable, Type, Union, Optional, Tuple


class SecurityError(Exception):
    """Base exception for security-related errors."""

    pass


class InputValidationError(SecurityError):
    """Raised when input validation fails."""

    pass


class AuthorizationError(SecurityError):
    """Raised when authorization checks fail."""

    pass


class SanitizationError(SecurityError):
    """Raised when data sanitization fails."""

    pass


class RateLimiter:
    """
    Rate limiting implementation to prevent DoS attacks.

    This class provides a context manager interface for rate limiting operations.
    It prevents more than `max_calls` operations within `time_window` seconds.
    """

    def __init__(self, max_calls: int = 100, time_window: int = 60):
        """
        Initialize a RateLimiter.

        Args:
            max_calls: Maximum number of calls allowed in the time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self._lock = threading.Lock()

    def __enter__(self):
        """
        Enter the context manager, checking if the rate limit has been exceeded.

        Raises:
            SecurityError: If the rate limit is exceeded
        """
        with self._lock:
            now = time.time()
            # Remove old calls
            self.calls = [t for t in self.calls if now - t < self.time_window]

            if len(self.calls) >= self.max_calls:
                raise SecurityError("Rate limit exceeded")

            self.calls.append(now)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass


class AuditLogger:
    """
    Secure audit logging implementation.

    This class provides a thread-safe way to log security-related events.
    """

    def __init__(self, log_file: str = "unicore_audit.log"):
        """
        Initialize an AuditLogger.

        Args:
            log_file: Path to the log file
        """
        self.log_file = log_file
        self._lock = threading.Lock()

    def log(self, event_type: str, details: str):
        """
        Securely log an event with timestamp and details.

        Args:
            event_type: Type of event (e.g., "LOGIN", "ACCESS_DENIED")
            details: Details of the event
        """
        with self._lock:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} - {event_type}: {details}\n"

            with open(self.log_file, "a") as f:
                f.write(log_entry)


def validate_type(
    value: Any,
    expected_types: Union[Type, Tuple[Type, ...]],
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


def validate_callable(func: Any, param_name: str = "parameter") -> Callable:
    """
    Validate that a parameter is callable and safe.

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

    # Check if function is bound method or regular function
    if hasattr(func, "__self__"):
        # Bound method - validate the instance
        validate_type(func.__self__, (object,), f"{param_name}.__self__")

    return func


def sanitize_string(
    value: Any, max_length: Optional[int] = None, allowed_chars: Optional[str] = None
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
