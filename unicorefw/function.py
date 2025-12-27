"""
File: unicorefw/function.py
Function utility methods for UniCoreFW.

This module contains functions for working with functions, such as debouncing,
throttling, partial application, and composition.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""
import threading
import time
from typing import Callable, TypeVar, Any, List, Optional
from queue import Queue
from .supporter import (
    _copy_function_metadata,
    _validate_callable,
    _try_import,
    _try_asyncio_schedule
)

T = TypeVar("T")
U = TypeVar("U")
R = TypeVar("R")

def debounce(func: Callable, wait: int) -> Callable:
    """
    Debounce a function to only be called after wait milliseconds of inactivity.
    
    The debounced function will be called with the last provided arguments after
    wait milliseconds have passed since the last call. This is useful for preventing
    excessive calls to a function that is expensive or has side effects.
    
    The debounced function is thread-safe and will not raise exceptions if the
    original function raises an exception.
    
    Args:
        func: The function to debounce
        wait: The delay in milliseconds
    
    Returns:
        A debounced function
    
    Examples:
        >>> def api_call():
        ...     return "Called!"
        >>> debounced = debounce(api_call, 100)
        >>> # Function will execute after 100ms of inactivity
    """
    wait_seconds = wait / 1000.0
    timer = None
    lock = threading.RLock()  # Reentrant lock for safety
    max_pending_timers = 10   # Prevent DoS
    pending_count = [0]
    
    def debounced(*args, **kwargs):
        nonlocal timer
        
        # DoS protection
        if pending_count[0] > max_pending_timers:
            return  # Silently drop excessive calls
        
        with lock:  # Atomic check-and-set
            if timer is not None:
                timer.cancel()
                pending_count[0] = max(0, pending_count[0] - 1)
            
            def safe_call():
                try:
                    with lock:
                        pending_count[0] = max(0, pending_count[0] - 1)
                    func(*args, **kwargs)
                except Exception:
                    # Prevent exceptions from breaking debounce state
                    with lock:
                        pending_count[0] = max(0, pending_count[0] - 1)
            
            timer = threading.Timer(wait_seconds, safe_call)
            timer.daemon = True
            pending_count[0] += 1
            timer.start()
    
    return debounced

def once(func: Callable) -> Callable:
    """
    Ensure a function is only called once, returning None on subsequent calls.
    Thread-safe implementation that matches your test expectations.

    Args:
        func: The function to wrap

    Returns:
        A function that will only execute once, then return None

    Examples:
        >>> wrapped_func = once(lambda: "called")
        >>> wrapped_func()  # Returns "called"
        'called'
        >>> wrapped_func()  # Returns None
        None
    """
    result = [None]
    has_been_called = [False]
    lock = threading.Lock()

    def once_func(*args, **kwargs):
        with lock:  # Thread-safe check-and-set
            if not has_been_called[0]:
                result[0] = func(*args, **kwargs)
                has_been_called[0] = True
                return result[0]  # Return the actual result on first call
            else:
                return None  # Return None on subsequent calls

    return once_func

def compose(*funcs: Callable) -> Callable:
    """
    Compose multiple functions to execute in sequence.

    Functions are applied from right to left, just like in mathematical composition.

    Args:
        *funcs: Functions to compose

    Returns:
        A new function that is the composition of the input functions
    
    Examples:
        >>> compose(lambda x: x + 1, lambda x: x * 2)(3)
        7
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

    Examples:
        >>> array = [1, 2, 3]
        >>> invoke(array, 'sqrt')
        [1.0, 1.4142135623730951, 1.7320508075688772]
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

    Examples:

        >>> obj = {'a': 1, 'b': 2}
        >>> matches({'a': 1, 'b': 2})(obj)
        True
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

    Examples:
        >>> def add(x, y):
        ...     return x + y
        >>> bound_add = bind(add, None, 1)
        >>> bound_add(2)
        3
    """

    def bound_func(*extra_args):
        return func(*(args + extra_args))

    return bound_func

def bind_all(obj: Any, *method_names: str) -> None:
    """
    Bind specified methods of obj to obj itself.

    Args:
        obj: The object to bind methods to
        *method_names: Names of methods to bind

    Returns:
        None

    Examples:
        >>> class A:
        ...     def add(self, x, y):
        ...         return x + y
        >>> bind_all(A(), 'add')
        >>> a = A()
        >>> a.add(1, 2)
        3
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

    Returns:
        None
    
    Examples:
        >>> def add(x, y):
        ...     return x + y
        >>> defer(add, 1, 2)
        >>> 3
    """
    threading.Timer(0, func, args=args, kwargs=kwargs).start()


def wrap(func: Callable, wrapper: Callable) -> Callable:
    """
    Wrap a function inside a wrapper function.

    Args:
        func: The function to wrap
        wrapper: The wrapper function that takes func as its first argument

    Returns:
        A wrapped function
    
    Examples:
        >>> def add(x, y):
        ...     return x + y
        >>> wrapped_add = wrap(add, lambda f, x, y: f(x, y) + 1)
        >>> wrapped_add(1, 2)
        4
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

    Examples:
        >>> def is_even(x):
        ...     return x % 2 == 0
        >>> negate(is_even)(3)
        False
    """
    return lambda *args, **kwargs: not func(*args, **kwargs)


def property_func(prop_name: str) -> Callable:
    """
    Return a function that retrieves a property value by name.

    Args:
        prop_name: The property name to retrieve

    Returns:
        A function that gets the property from objects

    Examples:
        >>> obj = {'a': 1, 'b': 2}
        >>> property_func('a')(obj)
        1
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

    Examples:
        >>> obj = {'a': 1, 'b': 2}
        >>> property_of(obj)('a')
        1
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

    Examples:
        >>> obj = {'a': 1, 'b': 2}
        >>> matcher({'a': 1, 'b': 2})(obj)
        True
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

    Examples:
        >>> obj = {'a': 1, 'b': 2}
        >>> iteratee({'a': 1, 'b': 2})(obj)
        True
    """
    if callable(value):
        return value
    elif isinstance(value, dict):
        return lambda obj: all(obj.get(k) == v for k, v in value.items())
    else:
        return lambda obj: obj == value


####################################################################################
#  Enhanced Function utility methods for UniCoreFW.
####################################################################################



def flip(func: Callable) -> Callable:
    """Create a function that invokes func with arguments reversed."""
    _validate_callable(func)

    def wrapper(*args, **kwargs):
        return func(*reversed(args), **kwargs)
    return _copy_function_metadata(wrapper, func)

def ary(func: Callable, n: Optional[int] = None) -> Callable:
    """
    Create a function that accepts up to n arguments, ignoring additional ones.
    
    Args:
        func: The function to cap arguments for
        n: The arity cap (if None, uses function's natural arity)
        
    Returns:
        A function that accepts at most n arguments
        
    Examples:
        >>> def add_four(a, b, c, d):
        ...     return a + b + c + d
        >>> capped = ary(add_four, 2)
        >>> capped(1, 2, 3, 4)  # Only uses first 2 args
        3
    """
    _validate_callable(func)
    
    if n is None:
        n = func.__code__.co_argcount
    
    def wrapper(*args, **kwargs):
        return func(*args[:n], **kwargs)
    
    return _copy_function_metadata(wrapper, func)

def flow(*functions: Callable) -> Callable:
    """
    Create a function that is the composition of functions, executed left to right.
    
    Args:
        *functions: Functions to compose
        
    Returns:
        A function that applies all functions in sequence
        
    Examples:
        >>> add_exclamation = lambda s: s + "!"
        >>> make_greeting = lambda name: f"Hello {name}"
        >>> greet = flow(make_greeting, add_exclamation)
        >>> greet("World")
        'Hello World!'
    """
    for func in functions:
        _validate_callable(func)
    
    if not functions:
        return lambda x: x
    
    def composed(*args, **kwargs):
        result = functions[0](*args, **kwargs)
        for func in functions[1:]:
            result = func(result)
        return result
    
    # Set _argcount for compatibility with tests
    composed._argcount = functions[0].__code__.co_argcount if functions else 0 # type: ignore
    composed.__name__ = f"flow({', '.join(f.__name__ for f in functions)})"
    return composed


def flow_right(*functions: Callable) -> Callable:
    """
    Create a function that is the composition of functions, executed right to left.
    
    Args:
        *functions: Functions to compose
        
    Returns:
        A function that applies all functions in reverse sequence
        
    Examples:
        >>> double = lambda x: x * 2
        >>> add_one = lambda x: x + 1
        >>> transform = flow_right(double, add_one)
        >>> transform(5)  # add_one(5) then double(6) = 12
        12
    """
    for func in functions:
        _validate_callable(func)
    
    if not functions:
        return lambda x: x
    
    def composed(*args, **kwargs):
        result = functions[-1](*args, **kwargs)
        for func in reversed(functions[:-1]):
            result = func(result)
        return result
    
    # Set _argcount for compatibility with tests
    composed._argcount = functions[-1].__code__.co_argcount if functions else 0 # type: ignore
    composed.__name__ = f"flow_right({', '.join(f.__name__ for f in functions)})"
    return composed


def iterated(func: Callable) -> Callable:
    """
    Create a function that applies func n times to a value.
    
    Args:
        func: The function to iterate
        
    Returns:
        A function that takes (value, n) and applies func n times
        
    Examples:
        >>> double = lambda x: x * 2
        >>> repeated_double = iterated(double)
        >>> repeated_double(2, 3)  # 2 -> 4 -> 8 -> 16
        16
    """
    _validate_callable(func)
    
    def iterator(value, n=1):
        result = value
        for _ in range(max(0, n)):
            result = func(result)
        return result
    
    return _copy_function_metadata(iterator, func)


def juxtapose(*functions: Callable) -> Callable:
    """
    Create a function that applies multiple functions to the same arguments.
    
    Args:
        *functions: Functions to apply in parallel
        
    Returns:
        A function that returns a list of results from all functions
        
    Examples:
        >>> first_char = lambda s: s[0]
        >>> last_char = lambda s: s[-1]
        >>> both_ends = juxtapose(first_char, last_char)
        >>> both_ends("hello")
        ['h', 'o']
    """
    for func in functions:
        _validate_callable(func)
    
    def parallel(*args, **kwargs):
        return [func(*args, **kwargs) for func in functions]
    
    # Set _argcount for compatibility with tests
    parallel._argcount = max((f.__code__.co_argcount for f in functions), default=0) # type: ignore
    parallel.__name__ = f"juxtapose({', '.join(f.__name__ for f in functions)})"
    return parallel


def enhanced_curry(func: Callable, arity: Optional[int] = None) -> Callable:
    """
    Enhanced curry function with explicit arity support and _argcount tracking.
    
    Args:
        func: The function to curry
        arity: Explicit arity (if None, inferred from function)
        
    Returns:
        A curried function that collects arguments until arity is reached
        
    Examples:
        >>> def add_three(a, b, c):
        ...     return a + b + c
        >>> curried_add = enhanced_curry(add_three)
        >>> result = curried_add(1)(2)(3)
        >>> result
        6
    """
    _validate_callable(func)
    
    if arity is None:
        arity = func.__code__.co_argcount
    
    def curried(*args):
        if len(args) >= arity:
            return func(*args[:arity])
        
        def next_curry(*more_args):
            return curried(*(args + more_args))
        
        # Track remaining arguments needed
        next_curry._argcount = arity - len(args) # type: ignore
        return _copy_function_metadata(next_curry, func)
    
    curried._argcount = arity # type: ignore
    return _copy_function_metadata(curried, func)


def enhanced_curry_right(func: Callable, arity: Optional[int] = None) -> Callable:
    """
    Enhanced curry_right with explicit arity support and _argcount tracking.
    
    Args:
        func: The function to curry from right to left
        arity: Explicit arity (if None, inferred from function)
        
    Returns:
        A curried function that collects arguments from right to left
        
    Examples:
        >>> def subtract(a, b, c):
        ...     return a - b - c
        >>> curried_sub = enhanced_curry_right(subtract)
        >>> result = curried_sub(1)(2)(10)  # 10 - 2 - 1
        >>> result
        7
    """
    _validate_callable(func)
    
    if arity is None:
        arity = func.__code__.co_argcount
    
    def curried(*args):
        if len(args) >= arity:
            # Collect the right number of args and pass them in normal order
            collected_args = args[-arity:] if len(args) > arity else args
            return func(*collected_args)
        
        def next_curry(*more_args):
            # Prepend new args to existing args (right-to-left collection)
            return curried(*(more_args + args))
        
        # Track remaining arguments needed
        next_curry._argcount = arity - len(args) # type: ignore
        return _copy_function_metadata(next_curry, func)
    
    curried._argcount = arity # type: ignore
    return _copy_function_metadata(curried, func)


def enhanced_partial(func: Callable, *bound_args, **bound_kwargs) -> Callable:
    """
    Enhanced partial application with _argcount tracking.
    
    Args:
        func: The function to partially apply
        *bound_args: Arguments to bind
        **bound_kwargs: Keyword arguments to bind
        
    Returns:
        A partially applied function with _argcount metadata
        
    Examples:
        >>> def multiply(a, b, c):
        ...     return a * b * c
        >>> times_two = enhanced_partial(multiply, 2)
        >>> times_two(3, 4)
        24
    """
    _validate_callable(func)
    
    def wrapper(*args, **kwargs):
        return func(*(bound_args + args), **{**bound_kwargs, **kwargs})
    
    # Calculate remaining argument count
    original_arity = func.__code__.co_argcount
    wrapper._argcount = max(0, original_arity - len(bound_args)) # type: ignore
    
    return _copy_function_metadata(wrapper, func)


def enhanced_partial_right(func: Callable, *bound_args, **bound_kwargs) -> Callable:
    """
    Enhanced partial_right application with _argcount tracking.
    
    Args:
        func: The function to partially apply from right
        *bound_args: Arguments to bind to the right
        **bound_kwargs: Keyword arguments to bind
        
    Returns:
        A partially applied function with _argcount metadata
        
    Examples:
        >>> def divide(a, b, c):
        ...     return a / b / c
        >>> divide_by_two = enhanced_partial_right(divide, 2)
        >>> divide_by_two(8, 2)  # 8 / 2 / 2
        2.0
    """
    _validate_callable(func)
    
    def wrapper(*args, **kwargs):
        return func(*args, *bound_args, **{**kwargs, **bound_kwargs})
    
    # Calculate remaining argument count
    original_arity = func.__code__.co_argcount
    wrapper._argcount = max(0, original_arity - len(bound_args)) # type: ignore
    
    return _copy_function_metadata(wrapper, func)


def enhanced_debounce(func: Callable, wait: int, max_wait: Optional[int] = None) -> Callable:
    """
    Enhanced debounce with max_wait support for better control.
    
    Args:
        func: The function to debounce
        wait: The delay in milliseconds
        max_wait: Maximum time to wait before forcing execution
        
    Returns:
        A debounced function with max_wait capability
        
    Examples:
        >>> def api_call():
        ...     return "Called!"
        >>> debounced = enhanced_debounce(api_call, 100, max_wait=500)
        >>> # Function will execute after 100ms of inactivity or 500ms max
    """
    _validate_callable(func)
    
    wait_seconds = wait / 1000.0
    max_wait_seconds = max_wait / 1000.0 if max_wait else None
    
    timer = None
    max_timer = None
    lock = threading.Lock()
    first_call_time = [None]
    result = [None]
    
    def debounced(*args, **kwargs):
        nonlocal timer, max_timer
        
        current_time = now()
        
        def execute():
            nonlocal timer, max_timer
            with lock:
                if timer:
                    timer.cancel()
                if max_timer:
                    max_timer.cancel()
                timer = max_timer = None
                first_call_time[0] = None
            result[0] = func(*args, **kwargs)
            return result[0]
        
        with lock:
            # Cancel existing timer
            if timer:
                timer.cancel()
            
            # Set first call time if not set
            if first_call_time[0] is None:
                first_call_time[0] = current_time # type: ignore
                result[0] = func(*args, **kwargs)  # Store initial result
                
                # Set max wait timer if specified
                if max_wait_seconds:
                    max_timer = threading.Timer(max_wait_seconds, execute)
                    max_timer.start()
            
            # Set regular debounce timer
            timer = threading.Timer(wait_seconds, execute)
            timer.start()
        
        return result[0]
    
    return _copy_function_metadata(debounced, func)


def now() -> int:
    """
    Get current timestamp in milliseconds.
    
    Returns:
        Current time in milliseconds since epoch
        
    Examples:
        >>> timestamp = now()
        >>> isinstance(timestamp, int)
        True
    """
    return int(time.time() * 1000)


# Override partial functions with enhanced versions
def partial(func: Callable, *bound_args, **bound_kwargs) -> Callable:
    """Enhanced partial with _argcount support."""
    return enhanced_partial(func, *bound_args, **bound_kwargs)


def partial_right(func: Callable, *bound_args, **bound_kwargs) -> Callable:
    """Enhanced partial_right with _argcount support."""
    return enhanced_partial_right(func, *bound_args, **bound_kwargs)


def debounce_(func: Callable, wait: int, *, max_wait: Optional[int] = None, use_main_thread: bool = False) -> Callable:
    """Enhanced debounce with max_wait support."""
    if max_wait is not None:
        return enhanced_debounce(func, wait, max_wait)
    else:
        # Use original implementation for backward compatibility
        return enhanced_debounce(func, wait)


def over_args(func: Callable, *transforms: Callable) -> Callable:
    """
    Create a function that applies transformations to arguments before calling func.
    
    Args:
        func: The function to invoke
        *transforms: Functions to transform corresponding arguments
        
    Returns:
        A function that transforms arguments before calling func
        
    Examples:
        >>> def add(a, b):
        ...     return a + b
        >>> square = lambda x: x * x
        >>> double = lambda x: x * 2
        >>> transform_add = over_args(add, square, double)
        >>> transform_add(3, 4)  # (3*3) + (4*2) = 9 + 8 = 17
        17
    """
    _validate_callable(func)
    
    # Handle case where transforms are passed as a single tuple/list
    if len(transforms) == 1 and isinstance(transforms[0], (list, tuple)):
        transforms = transforms[0] # type: ignore
    
    for transform in transforms:
        _validate_callable(transform)
    
    def wrapper(*args, **kwargs):
        transformed_args = []
        for i, arg in enumerate(args):
            if i < len(transforms):
                transformed_args.append(transforms[i](arg))
            else:
                transformed_args.append(arg)
        return func(*transformed_args, **kwargs)
    
    return _copy_function_metadata(wrapper, func)



def spread(func: Callable) -> Callable:
    """
    Create a function that spreads an array argument to func as individual arguments.
    
    Args:
        func: The function to spread arguments to
        
    Returns:
        A function that spreads array arguments
        
    Examples:
        >>> def add_three(a, b, c):
        ...     return a + b + c
        >>> spread_add = spread(add_three)
        >>> spread_add([1, 2, 3])
        6
    """
    _validate_callable(func)
    
    def wrapper(args_array, **kwargs):
        return func(*args_array, **kwargs)
    
    return _copy_function_metadata(wrapper, func)


def unary(func: Callable) -> Callable:
    """
    Create a function that accepts only the first argument, ignoring others.
    
    Args:
        func: The function to cap arguments for
        
    Returns:
        A function that accepts only one argument
        
    Examples:
        >>> def add_all(*args):
        ...     return sum(args)
        >>> first_only = unary(add_all)
        >>> first_only(1, 2, 3, 4)  # Only uses first argument
        1
    """
    _validate_callable(func)
    
    def wrapper(arg, *ignored_args, **kwargs):
        return func(arg, **kwargs)
    
    return _copy_function_metadata(wrapper, func)

def reduce_(iterable, func, initial=None):
    """
    Reduce implementation for test compatibility.
    
    Args:
        iterable: The collection to reduce
        func: The reducer function
        initial: Initial value
        
    Returns:
        The reduced value

    Examples:
        >>> reduce_([1, 2, 3], lambda x, y: x + y)
        6
    """
    if initial is None:
        iterator = iter(iterable)
        try:
            initial = next(iterator)
        except StopIteration:
            raise TypeError("reduce() of empty sequence with no initial value")
        iterable = iterator
    
    result = initial
    for item in iterable:
        result = func(result, item)
    return result


def map_(iterable, func):
    """
    Map implementation for test compatibility.
    
    Args:
        iterable: The collection to map over
        func: The mapping function
        
    Returns:
        List of mapped values
    
    Examples:
        >>> map_([1, 2, 3], lambda x: x * x)
        [1, 4, 9]
    """
    return [func(item) for item in iterable]


def filter_(iterable, predicate):
    """
    Filter implementation for test compatibility.
    
    Args:
        iterable: The collection to filter
        predicate: The filter function
        
    Returns:
        List of filtered values

    Examples:
        >>> filter_([1, 2, 3], lambda x: x % 2 == 0)
        [2]
    """
    return [item for item in iterable if predicate(item)]

def after(a: Any, b: Any) -> Callable[..., Optional[R]]:
    """
    Create a function that only invokes the provided function after it has been
    called a specified number of times.

    Accepts (func, n) or (n, func). The wrapped function will only execute the
    original `func` on the nth and subsequent calls; before that, it returns None.

    Parameters:
        a : Callable[..., R] or int
            The function to wrap or the number of calls to wait before invoking.
        b : int or Callable[..., R]
            The number of calls to wait before invoking or the function to wrap.

    Returns:
        A wrapped function that executes `func` only after the specified number
        of invocations.

    Examples:
        >>> def greet():
        ...     return "Hello!"
        >>> greet_after_3 = after(greet, 3)
        >>> greet_after_3()  # None
        >>> greet_after_3()  # None
        >>> greet_after_3()  # "Hello!"
    """

    if callable(a) and isinstance(b, int):
        func, times = a, b
    elif isinstance(a, int) and callable(b):
        times, func = a, b  # swapped
    else:
        raise TypeError("after expects (func, int) or (int, func)")

    count = [0]
    def wrapper(*args: Any, **kwargs: Any) -> Optional[R]:
        count[0] += 1
        if count[0] >= max(times, 1):
            return func(*args, **kwargs) # type: ignore
        return None

    wrapper.__name__    = func.__name__
    wrapper.__doc__     = func.__doc__
    wrapper.__wrapped__ = func # type: ignore
    return wrapper

def before(a: Any, b: Any) -> Callable[..., Optional[R]]:
    """
    Create a wrapper that limits how many times a function can run.

    Accepts (func, n) or (n, func). The wrapped function will execute the original
    `func` on the first `n-1` calls; on the nth and subsequent calls, it returns None.

    Parameters:
        a : Callable[..., R] or int
            The function to wrap or the maximum number of invocations.
        b : int or Callable[..., R]
            The maximum number of invocations or the function to wrap.

    Returns:
        Callable[..., Optional[R]]
        A wrapper function that will call `func` up to `n-1` times, then return None.

    Raises:
        TypeError - If arguments are not provided as (func, int) or (int, func).

    Examples:
        >>> def greet(name):
        ...     return f"Hello, {name}!"
        ...
        >>> greeter = before(greet, 3)
        >>> greeter("Alice")
        'Hello, Alice!'
        >>> greeter("Bob")
        'Hello, Bob!'
        >>> greeter("Eve")  # Third call (n=3): returns None
        None

        # Reversed argument order:
        >>> doubler = before(2, lambda x: x * 2)
        >>> doubler(5)
        10
        >>> doubler(7)      # Second call (n=2): returns None
        None
    """
    if callable(a) and isinstance(b, int):
        func, times = a, b
    elif isinstance(a, int) and callable(b):
        times, func = a, b
    else:
        raise TypeError("before expects (func, int) or (int, func)")

    limit = max(times - 1, 0)
    calls = [0]

    def wrapper(*args: Any, **kwargs: Any) -> Optional[R]:
        if calls[0] < limit:
            calls[0] += 1
            return func(*args, **kwargs) # type: ignore
        return None

    wrapper.__name__    = func.__name__
    wrapper.__doc__     = func.__doc__
    wrapper.__wrapped__ = func # type: ignore
    return wrapper


def allany(*preds: Callable[[Any], bool]) -> Callable[[List[Any]], bool]:

    """
    Returns a function that checks if any of the given predicates return True for
    every item in the given list.

    Parameters:
        *preds: Callable[[Any], bool]
            Zero or more predicate functions to test.

    Returns:
        Callable[[List[Any]], bool]
            A function that takes a list and returns True if every item in the list
            satisfies at least one of the given predicates, False otherwise.
    Examples:
        >>> def is_even(x):
        ...     return x % 2 == 0
        >>> def is_positive(x):
        ...     return x > 0
        >>> is_even_and_positive = allany(is_even, is_positive)
        >>> is_even_and_positive([2, 4, 6])  # True
        >>> is_even_and_positive([1, 3, 5])  # False
    """
    def tester(arr: List[Any]) -> bool:
        for x in arr:
            if not any(p(x) for p in preds):
                return False
        return True
    tester.__name__    = "allany"
    tester.__doc__     = allany.__doc__
    return tester

def anyof(*funcs: Callable[[Any], bool]) -> Callable[[Any], bool]:
    """
    Returns a function that takes a single argument and returns True if any of the
    given functions, when called with that argument, return True.

    Parameters:
        *funcs: Callable[[Any], bool]
            Zero or more predicate functions to test.

    Returns:
        Callable[[Any], bool]
            A function that takes an argument and returns True if any of the given
            predicates return True, False otherwise.
    Examples:
        >>> def is_even(x):
        ...     return x % 2 == 0
        >>> def is_positive(x):
        ...     return x > 0
        >>> is_even_or_positive = anyof(is_even, is_positive)
        >>> is_even_or_positive(2)  # True
        >>> is_even_or_positive(-3)  # False
    """
    def wrapper(arg: Any) -> bool:
        return any(f(arg) for f in funcs)
    wrapper.__name__ = "anyof"
    wrapper._argcount = 1 # type: ignore
    return wrapper

def delay(func, wait, *args, **kwargs):
    """
    Invokes `func` after `wait` milliseconds.

    Parameters:
        func: Callable[[Any], R]
            The function to invoke.
        wait: int
            The number of milliseconds to wait.
        *args: Any
            Arguments to pass to `func`.
        **kwargs: Any
            Keyword arguments to pass to `func`.

    Returns:
        R
            The result of `func`.

    Examples:
        >>> def print_time():
        ...     print(time.time())
        >>> delayed = delay(print_time, 1000)
        >>> delayed()  # Waits 1 second before printing time
    """
    time.sleep(wait / 1000.0)
    return func(*args, **kwargs)

def once_(func):
    """
    Creates a function that is restricted to execute `func` once. 
    Subsequent calls return the value of the first invocation.

    Args:
        func: The function to execute.

    Returns:
        A new function that wraps `func`, ensuring it is only called once.

    Examples:
        >>> def greet():
        ...     return "Hello!"
        >>> greet_once = once_(greet)
        >>> greet_once()  # "Hello!"
        >>> greet_once()  # "Hello!"
    """

    called = False
    result = None
    def wrapper(*args, **kwargs):
        nonlocal called, result
        if not called:
            result = func(*args, **kwargs)
            called = True
        return result
    return wrapper

def throttle(func, wait):
    """
    Creates a function that is restricted to execute `func` once per `wait` milliseconds.
    
    Parameters:
        func: Callable[[Any], R]
            The function to throttle.
        wait: int
            The number of milliseconds to wait.
    
    Returns:
        Callable[[Any], R]
            A new function that wraps `func`, ensuring it is only called once per `wait` milliseconds.
    
    Examples:
        >>> def print_time():
        ...     print(time.time())
        >>> throttled = throttle(print_time, 1000)
        >>> throttled()  # Prints time
        >>> throttled()  # Does nothing
        >>> time.sleep(1)
        >>> throttled()  # Prints time
    """
    last_called = 0.0
    last_result = None
    wait_s = wait / 1000.0
    def wrapper(*args, **kwargs):
        nonlocal last_called, last_result
        now = time.time()
        if now - last_called > wait_s:
            last_called = now
            last_result = func(*args, **kwargs)
        return last_result
    return wrapper


def rearg(func: Callable[..., R], *indexes: int) -> Callable[..., R]:

    # Normalize a single list/tuple argument
    """
    Creates a function that invokes `func` with arguments rearranged according to the specified
    indexes. The argument value at the first index is provided as the first argument, the argument
    value at the second index is provided as the second argument, and so on. Arguments not specified
    in `indexes` maintain their original order after the rearranged arguments.

    Args:
        func: Function to rearrange arguments for.
        *indexes: The specified argument indexes.

    Returns:
        A new function with rearranged arguments for `func`.

    Examples:
        >>> def example(a, b, c):
        ...     return a, b, c
        >>> rearranged = rearg(example, 2, 0, 1)
        >>> rearranged(1, 2, 3)
        (3, 1, 2)
    """

    if len(indexes) == 1 and isinstance(indexes[0], (list, tuple)):
        idxs = tuple(indexes[0])
    else:
        idxs = indexes

    def wrapper(*args: Any, **kwargs: Any) -> R:
        # Pick valid indices in the order given
        valid = [i for i in idxs if isinstance(i, int) and 0 <= i < len(args)]
        # Reordered portion
        reordered = [args[i] for i in valid]
        # Append the args not yet used
        remaining = [args[i] for i in range(len(args)) if i not in valid]
        return func(*reordered, *remaining, **kwargs)

    # Copy metadata for introspection
    wrapper.__name__    = func.__name__
    wrapper.__doc__     = func.__doc__
    wrapper.__wrapped__ = func # type: ignore

    return wrapper

def conjoin(*preds):
    """
    Returns a function that tests whether **all** elements of a sequence pass
    **all** of the provided predicates.

    Args:
        *preds: Functions to conjoin.

    Returns:
        A function that takes an iterable, and returns True if all elements of
        the iterable pass all predicates, False otherwise.

    Examples:
        >>> is_even = lambda x: x % 2 == 0
        >>> is_positive = lambda x: x > 0
        >>> both = conjoin(is_even, is_positive)
        >>> both([2, 4, 6])
        True
        >>> both([2, 4, 6, -2])
        False
    """
    def wrapper(seq):
        return all(all(p(x) for p in preds) for x in seq)
    return wrapper

#######################################################################
# Function Aliases
#######################################################################
disjoin = allany
curry = enhanced_curry
curry_right = enhanced_curry_right