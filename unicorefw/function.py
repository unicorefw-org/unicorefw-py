"""
Function utility methods for UniCoreFW.

This module contains functions for working with functions, such as debouncing,
throttling, partial application, and composition.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info
"""

import threading
import time
from typing import Callable, TypeVar, Any, Optional, List

T = TypeVar("T")
U = TypeVar("U")


def partial(func: Callable, *partial_args) -> Callable:
    """
    Partially apply arguments to a function.

    Args:
        func: The function to partially apply
        *partial_args: The arguments to pre-fill

    Returns:
        A new function with some arguments pre-filled
    """

    def partially_applied(*extra_args):
        return func(*(partial_args + extra_args))

    return partially_applied


def throttle(func: Callable, wait: int) -> Callable:
    """
    Throttle a function to be called at most once every wait milliseconds.

    Args:
        func: The function to throttle
        wait: The minimum time in milliseconds between function calls

    Returns:
        A throttled function
    """
    last_called = [0]  # Using a list for mutable closure

    def throttled_func(*args, **kwargs):
        now = time.time()
        if now - last_called[0] > wait / 1000:
            last_called[0] = now
            return func(*args, **kwargs)
        return None  # Return None when not calling the function

    return throttled_func


def debounce(func: Callable, wait: int, *, use_main_thread: bool = False) -> Callable:
    """
    Debounce a function to only be called after wait milliseconds of inactivity.

    Args:
        func: The function to debounce
        wait: The delay in milliseconds
        use_main_thread: If True, ensures the function is called in the main thread

    Returns:
        A debounced function
    """
    wait_seconds = wait / 1000.0
    timer = None
    lock = threading.Lock()

    def debounced(*args, **kwargs):
        nonlocal timer

        def call_func():
            if use_main_thread:
                # Queue the function to be called in the main thread
                threading.main_thread().run(func, *args, **kwargs)
            else:
                func(*args, **kwargs)

        with lock:
            if timer is not None:
                timer.cancel()
            timer = threading.Timer(wait_seconds, call_func)
            timer.start()

    return debounced


def once(func: Callable) -> Callable:
    """
    Ensure a function is only called once, returning None on subsequent calls.

    Args:
        func: The function to wrap

    Returns:
        A function that will only execute once
    """
    result = [None]  # Using a list for mutable closure
    has_been_called = [False]

    def once_func(*args, **kwargs):
        if not has_been_called[0]:
            result[0] = func(*args, **kwargs)
            has_been_called[0] = True
        else:
            result[0] = None  # Return None after the first call
        return result[0]

    return once_func


def after(times: int, func: Callable) -> Callable:
    """
    Return a function that will only run after it's been called a specified number of times.

    Args:
        times: Number of calls before the function executes
        func: The function to wrap

    Returns:
        A function that only executes after being called 'times' times
    """
    calls = [0]  # Using a list for mutable closure

    def after_func(*args, **kwargs):
        calls[0] += 1
        if calls[0] >= times:
            return func(*args, **kwargs)
        return None

    return after_func


def compose(*funcs: Callable) -> Callable:
    """
    Compose multiple functions to execute in sequence.

    Functions are applied from right to left, just like in mathematical composition.

    Args:
        *funcs: Functions to compose

    Returns:
        A new function that is the composition of the input functions
    """

    def composed(value):
        for func in reversed(funcs):
            value = func(value)
        return value

    return composed


def invoke(array: List[Any], func_name: str, *args) -> List[Any]:
    """
    Call a method on each item in an array.

    Args:
        array: The array of objects
        func_name: The method name to call on each object
        *args: Arguments to pass to the method

    Returns:
        A list of method call results
    """
    return [
        getattr(item, func_name)(*args) if hasattr(item, func_name) else None
        for item in array
    ]


def matches(attrs: dict) -> Callable:
    """
    Return a function that checks if an object matches key-value pairs.

    Args:
        attrs: The attributes to match

    Returns:
        A function that checks if objects match the attributes
    """

    def match(obj):
        return all(obj.get(k) == v for k, v in attrs.items())

    return match


def bind(func: Callable, context: Any, *args) -> Callable:
    """
    Bind a function to a context with optional pre-filled arguments.

    Args:
        func: The function to bind
        context: The context to bind to (not used in Python implementation)
        *args: Arguments to pre-fill

    Returns:
        A bound function
    """

    def bound_func(*extra_args):
        return func(*(args + extra_args))

    return bound_func


def before(n: int, func: Callable) -> Callable:
    """
    Return a function that can be called up to n times.

    Args:
        n: Maximum number of times to call the function
        func: The function to wrap

    Returns:
        A function that will execute at most n times
    """
    result = [None]  # Using a list for mutable closure
    calls = [0]

    def limited_func(*args, **kwargs):
        if calls[0] < n:
            result[0] = func(*args, **kwargs)
            calls[0] += 1
        return result[0]

    return limited_func


def bind_all(obj: Any, *method_names: str) -> None:
    """
    Bind specified methods of obj to obj itself.

    Args:
        obj: The object to bind methods to
        *method_names: Names of methods to bind
    """
    for method_name in method_names:
        if hasattr(obj, method_name):
            bound_method = getattr(obj, method_name).__get__(obj)
            setattr(obj, method_name, bound_method)


def defer(func: Callable, *args, **kwargs) -> None:
    """
    Defer invoking the function until the current call stack has cleared.

    Args:
        func: The function to defer
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    """
    threading.Timer(0, func, args=args, kwargs=kwargs).start()


def delay(func: Callable, wait: int, *args, **kwargs) -> None:
    """
    Invoke func after a specified number of milliseconds.

    Args:
        func: The function to delay
        wait: The delay in milliseconds
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    """
    threading.Timer(wait / 1000, func, args=args, kwargs=kwargs).start()


def wrap(func: Callable, wrapper: Callable) -> Callable:
    """
    Wrap a function inside a wrapper function.

    Args:
        func: The function to wrap
        wrapper: The wrapper function that takes func as its first argument

    Returns:
        A wrapped function
    """

    def wrapped(*args, **kwargs):
        return wrapper(func, *args, **kwargs)

    return wrapped


def negate(func: Callable) -> Callable:
    """
    Return the negation of a predicate function.

    Args:
        func: The predicate function to negate

    Returns:
        A function that returns the opposite of the original function
    """
    return lambda *args, **kwargs: not func(*args, **kwargs)


def property_func(prop_name: str) -> Callable:
    """
    Return a function that retrieves a property value by name.

    Args:
        prop_name: The property name to retrieve

    Returns:
        A function that gets the property from objects
    """
    return (
        lambda obj: obj.get(prop_name)
        if isinstance(obj, dict)
        else getattr(obj, prop_name, None)
    )


def property_of(obj: Any) -> Callable:
    """
    Return a function that retrieves a property value from a given object.

    Args:
        obj: The object to get properties from

    Returns:
        A function that gets properties from the object
    """
    return (
        lambda prop_name: obj.get(prop_name)
        if isinstance(obj, dict)
        else getattr(obj, prop_name, None)
    )


def matcher(attrs: dict) -> Callable:
    """
    Return a function that checks if an object has matching key-value pairs.

    Args:
        attrs: The attributes to match

    Returns:
        A function that checks if objects match the attributes
    """

    def match(obj):
        return all(obj.get(k) == v for k, v in attrs.items())

    return match


def iteratee(value: Any) -> Callable:
    """
    Return a function based on the type of value.

    If value is callable, returns it directly.
    If value is a dict, returns a matcher function.
    Otherwise, returns an identity function that checks for equality.

    Args:
        value: The value to convert to a function

    Returns:
        A function based on the value type
    """
    if callable(value):
        return value
    elif isinstance(value, dict):
        return lambda obj: all(obj.get(k) == v for k, v in value.items())
    else:
        return lambda obj: obj == value
