"""
File: unicorefw/utils.py
General utility functions for UniCoreFW.

This module contains miscellaneous utility functions that don't fit into other categories.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""

import functools
import random as random_module
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, List, Optional, TypeVar

from .security import (
    InputValidationError,
    ResourceLimitError,
    _estimate_resource_weight,
    _validate_resource_duration,
    _validate_resource_limit,
    _validate_resource_ratio,
)

_DEFAULT_MAX_DECOMPRESS_INPUT_LENGTH = 1_000_000
_DEFAULT_MAX_DECOMPRESS_OUTPUT_LENGTH = 1_000_000
_DEFAULT_MAX_DECOMPRESS_RATIO = 100.0
_HARD_MAX_DECOMPRESS_INPUT_LENGTH = 4_000_000
_HARD_MAX_DECOMPRESS_OUTPUT_LENGTH = 64_000_000
_HARD_MAX_DECOMPRESS_RATIO = 1_000.0
_DEFAULT_MEMOIZE_MAX_ENTRIES = 256
_DEFAULT_MEMOIZE_MAX_WEIGHT_BYTES = 16 * 1024 * 1024
_DEFAULT_MEMOIZE_TTL_SECONDS = 300.0
_HARD_MAX_MEMOIZE_ENTRIES = 100_000
_HARD_MAX_MEMOIZE_WEIGHT_BYTES = 256 * 1024 * 1024
_HARD_MAX_MEMOIZE_TTL_SECONDS = 7 * 24 * 60 * 60

T = TypeVar("T")
U = TypeVar("U")


def identity(value: T) -> T:
    """
    Return the given value unchanged.

    Args:
        value: The value to return

    Returns:
        The same value that was passed in

    Examples:
        >>> identity(42)
        42
    """
    return value


def times(n: int, func: Callable[[int], T]) -> List[T]:
    """
    Call the given function `n` times, passing the iteration index to `func`.

    Args:
        n: Number of times to call the function
        func: A function that takes the index as an argument

    Returns:
        A list of the results

    Examples:
        >>> times(3, lambda x: x * x)
        [0, 1, 4]
    """
    return [func(i) for i in range(n)]


def unique_id(prefix: str = "") -> str:
    """
    Generate a unique identifier with an optional prefix.

    This function uses a global counter to ensure uniqueness within a single process.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        A unique string identifier

    Examples:
        >>> unique_id("user-")
        "user-1"
        >>> unique_id("user-")
        "user-2"
    """
    # This is a module-level function, so we need to access the class variable directly
    # from the UniCoreFW class. This will be properly imported and resolved at runtime.
    from .core import UniCoreFW

    UniCoreFW._id_counter += 1
    return f"{prefix}{UniCoreFW._id_counter}"


def mixin(obj):
    """
    Adds properties of an object as functions on UniCoreFW.

    This function dynamically adds methods to the UniCoreFW class. This is useful for
    adding custom functions to the library without having to modify the source code.

    Args:
        obj: An object with properties to add to UniCoreFW

    Examples:
        >>> mixin({"triple": lambda x: x * 3, "quadruple": lambda x: x * 4})
        >>> print(UniCoreFW.triple(3))  # Output: 9
        >>> print(UniCoreFW.quadruple(2))  # Output: 8
    """
    from .core import UniCoreFW

    for key, func in obj.items():
        if callable(func):
            setattr(UniCoreFW, key, func)


def now() -> int:
    """
    Return the current timestamp in milliseconds.

    Returns:
        The current time as milliseconds since epoch

    Examples:
        >>> now()
        1680000000000
    """
    return int(time.time() * 1000)


def memoize(
    func: Callable,
    *,
    max_entries: int = _DEFAULT_MEMOIZE_MAX_ENTRIES,
    max_weight_bytes: int = _DEFAULT_MEMOIZE_MAX_WEIGHT_BYTES,
    ttl_seconds: float = _DEFAULT_MEMOIZE_TTL_SECONDS,
    clock: Callable[[], float] = time.monotonic,
) -> Callable:
    """
    Cache positional calls in a bounded, thread-safe LRU.

    Args:
        func: The function to memoize
        max_entries: Maximum cached call count
        max_weight_bytes: Maximum estimated key and result weight
        ttl_seconds: Maximum age of one cache entry
        clock: Monotonic clock used for deterministic expiry

    Returns:
        A memoized version of the function

    Examples:
        >>> memoize(lambda x: x * 2)(5)
        10
    """
    if not callable(func):
        raise InputValidationError("func must be callable")
    if not callable(clock):
        raise InputValidationError("clock must be callable")
    entry_limit = _validate_resource_limit(
        max_entries,
        "max_entries",
        _HARD_MAX_MEMOIZE_ENTRIES,
    )
    weight_limit = _validate_resource_limit(
        max_weight_bytes,
        "max_weight_bytes",
        _HARD_MAX_MEMOIZE_WEIGHT_BYTES,
    )
    ttl_limit = _validate_resource_duration(
        ttl_seconds,
        "ttl_seconds",
        _HARD_MAX_MEMOIZE_TTL_SECONDS,
    )

    cache = OrderedDict()
    lock = threading.RLock()
    total_weight = 0

    def remove_entry(key: Any) -> None:
        nonlocal total_weight
        _, _, weight = cache.pop(key)
        total_weight -= weight

    def prune_expired(current_time: float) -> None:
        for key, (_, expires_at, _) in list(cache.items()):
            if expires_at <= current_time:
                remove_entry(key)

    @functools.wraps(func)
    def memoized_func(*args):
        nonlocal total_weight
        hash(args)
        current_time = clock()
        with lock:
            cached = cache.get(args)
            if cached is not None:
                result, expires_at, _ = cached
                if expires_at > current_time:
                    cache.move_to_end(args)
                    return result
                remove_entry(args)

        result = func(*args)
        key_weight = _estimate_resource_weight(args, weight_limit)
        if key_weight > weight_limit:
            return result
        result_weight = _estimate_resource_weight(
            result,
            weight_limit - key_weight,
        )
        entry_weight = key_weight + result_weight
        if entry_weight > weight_limit:
            return result

        current_time = clock()
        with lock:
            prune_expired(current_time)
            cached = cache.get(args)
            if cached is not None:
                cached_result, expires_at, _ = cached
                if expires_at > current_time:
                    cache.move_to_end(args)
                    return cached_result
                remove_entry(args)

            while cache and (
                len(cache) >= entry_limit or total_weight + entry_weight > weight_limit
            ):
                oldest_key = next(iter(cache))
                remove_entry(oldest_key)
            cache[args] = (result, current_time + ttl_limit, entry_weight)
            total_weight += entry_weight
        return result

    def cache_clear() -> None:
        nonlocal total_weight
        with lock:
            cache.clear()
            total_weight = 0

    def cache_info() -> dict:
        with lock:
            prune_expired(clock())
            return {
                "entries": len(cache),
                "max_entries": entry_limit,
                "weight_bytes": total_weight,
                "max_weight_bytes": weight_limit,
                "ttl_seconds": ttl_limit,
            }

    memoized_func.cache_clear = cache_clear  # type: ignore[attr-defined]
    memoized_func.cache_info = cache_info  # type: ignore[attr-defined]

    return memoized_func


def random(min_val: int, max_val: int) -> int:
    """
    Return a random integer between min_val and max_val, inclusive.

    Args:
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)

    Returns:
        A random integer

    Examples:
        >>> random(1, 10)
        5
    """
    return random_module.randint(min_val, max_val)


def tap(value: T, func: Callable[[T], Any]) -> T:
    """
    Invoke func with the value and then return value.

    Args:
        value: The value to pass to func and return
        func: A function to call with value

    Returns:
        The original value

    Examples:
        >>> tap(42, print)
        42
    """
    func(value)
    return value


def constant(value: T) -> Callable[[], T]:
    """
    Return a function that always returns the specified value.

    Args:
        value: The value to return

    Returns:
        A function that always returns the value

    Examples:
        >>> constant(42)
        42
    """
    return lambda: value


def noop() -> None:
    """
    A function that does nothing (no operation).

    Returns:
        None

    Examples:
        >>> noop()
        None
    """
    pass


def compress(word: str) -> str:
    """
    Compress a string using a simple run-length encoding.

    This method compresses the input string by replacing sequences of repeated characters
    with a single instance of the character followed by a number indicating the count
    of repetitions.

    Args:
        word: The input string to be compressed

    Returns:
        A compressed version of the input string

    Examples:
        >>> compress("aaabbbccc")
        '3a3b3c'
    """
    if not word:
        return ""

    comp = []  # Use a list for faster concatenation
    length = len(word)
    i = 0

    while i < length:
        count = 1
        # Count up to 9 consecutive characters
        while i + count < length and word[i] == word[i + count] and count < 9:
            count += 1

        # Append the count and character to comp
        comp.append(f"{count}{word[i]}")

        # Move to the next distinct character
        i += count

    return "".join(comp)  # Join the list into a single string at the end


def decompress(
    comp: str,
    *,
    max_input_length: int = _DEFAULT_MAX_DECOMPRESS_INPUT_LENGTH,
    max_output_length: int = _DEFAULT_MAX_DECOMPRESS_OUTPUT_LENGTH,
    max_compression_ratio: float = _DEFAULT_MAX_DECOMPRESS_RATIO,
) -> str:
    """
    Decompress a given string, which is compressed using run-length encoding.

    Args:
        comp: The compressed string to be decompressed
        max_input_length: Maximum compressed character count
        max_output_length: Maximum decompressed character count
        max_compression_ratio: Maximum output-to-input character ratio

    Returns:
        The decompressed string

    Raises:
        ResourceLimitError: If input, output, or expansion exceeds its budget
        InputValidationError: If a limit setting is invalid

    Examples:
        >>> decompress("2a3b4c")
        'aabbbcccc'
    """
    if not isinstance(comp, str):
        raise TypeError("comp must be a string")
    input_limit = _validate_resource_limit(
        max_input_length,
        "max_input_length",
        _HARD_MAX_DECOMPRESS_INPUT_LENGTH,
    )
    output_limit = _validate_resource_limit(
        max_output_length,
        "max_output_length",
        _HARD_MAX_DECOMPRESS_OUTPUT_LENGTH,
    )
    ratio_limit = _validate_resource_ratio(
        max_compression_ratio,
        "max_compression_ratio",
        _HARD_MAX_DECOMPRESS_RATIO,
    )
    if len(comp) > input_limit:
        raise ResourceLimitError(
            "compressed input length",
            input_limit,
            len(comp),
        )

    result = []
    output_length = 0
    i = 0

    while i < len(comp):
        # Extract the number (count of characters)
        count = 0
        while i < len(comp) and comp[i].isdigit():
            digit = ord(comp[i]) - ord("0")
            remaining_output = output_limit - output_length
            if count > (remaining_output - digit) // 10:
                raise ResourceLimitError(
                    "decompressed output length",
                    output_limit,
                )
            count = count * 10 + digit
            i += 1

        # Extract the character
        if i < len(comp):
            char = comp[i]
            prospective_length = output_length + count
            if prospective_length > output_limit:
                raise ResourceLimitError(
                    "decompressed output length",
                    output_limit,
                    prospective_length,
                )
            if comp and prospective_length / len(comp) > ratio_limit:
                raise ResourceLimitError(
                    "compression ratio",
                    ratio_limit,
                    prospective_length / len(comp),
                )
            result.append(char * count)
            output_length = prospective_length
            i += 1

    return "".join(result)


def max_value(
    array: List[T], key_func: Optional[Callable[[T], Any]] = None
) -> Optional[T]:
    """
    Return the maximum value in the array, based on an optional key function.

    Args:
        array: The array to search
        key_func: Optional function to determine the comparison key

    Returns:
        The maximum value or None if array is empty

    Examples:
        >>> max_value([1, 2, 3], key=lambda x: -x)
        1
    """
    if not array:
        return None
    if key_func:
        return max(array, key=key_func)
    return max(array)  # type: ignore


def min_value(
    array: List[T], key_func: Optional[Callable[[T], Any]] = None
) -> Optional[T]:
    """
    Return the minimum value in the array, based on an optional key function.

    Args:
        array: The array to search
        key_func: Optional function to determine the comparison key

    Returns:
        The minimum value or None if array is empty

    Examples:
        >>> min_value([1, 2, 3], key=lambda x: -x)
        3
    """
    if not array:
        return None
    if key_func:
        return min(array, key=key_func)
    return min(array)  # type: ignore


def some(array: List[T], func: Callable[[T], bool]) -> bool:
    """
    Check if at least one element in the array matches the predicate.

    Args:
        array: The array to check
        func: A predicate function

    Returns:
        True if any element matches, False otherwise

    Examples:
        >>> some([1, 2, 3], lambda x: x > 0)
        True
    """
    return any(func(x) for x in array)


def every(array: List[T], func: Callable[[T], bool]) -> bool:
    """
    Check if every element in the array matches the predicate.

    Args:
        array: The array to check
        func: A predicate function

    Returns:
        True if all elements match, False otherwise

    Examples:
        >>> every([1, 2, 3], lambda x: x > 0)
        True
    """
    return all(func(x) for x in array)


def chain(obj: Any) -> Any:
    """
    Enable chaining by wrapping the object in a chainable class.

    Args:
        obj: The object to wrap

    Returns:
        A chainable wrapper

    Examples:
        >>> chain({"a": 1, "b": 2})["a"]
        1
    """
    # Import locally to avoid circular imports
    from .core import UniCoreFWWrapper

    return UniCoreFWWrapper(obj)
