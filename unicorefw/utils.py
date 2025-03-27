"""
General utility functions for UniCoreFW.

This module contains miscellaneous utility functions that don't fit into other categories.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info
"""

import time
import random as random_module
from typing import Any, Callable, List, TypeVar, Union, Optional, Dict, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from .core import UniCoreFWWrapper

T = TypeVar('T')
U = TypeVar('U')

def identity(value: T) -> T:
    """
    Return the given value unchanged.
    
    Args:
        value: The value to return
        
    Returns:
        The same value that was passed in
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
    """
    # This is a module-level function, so we need to access the class variable directly
    # from the UniCoreFW class. This will be properly imported and resolved at runtime.
    from .core import UniCoreFW
    UniCoreFW._id_counter += 1
    return f"{prefix}{UniCoreFW._id_counter}"

def escape(string: str) -> str:
    """
    Escape HTML characters in a string.
    
    Args:
        string: The string to escape
        
    Returns:
        An HTML-escaped string
    """
    escape_map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
        "`": "&#x60;",
    }
    return "".join(escape_map.get(c, c) for c in string)

def mixin(obj):
    """
    Adds properties of an object as functions on UniCoreFW.
    
    This function dynamically adds methods to the UniCoreFW class. This is useful for
    adding custom functions to the library without having to modify the source code.
    
    Args:
        obj: An object with properties to add to UniCoreFW
    """
    from .core import UniCoreFW
    for key, func in obj.items():
        if callable(func):
            setattr(UniCoreFW, key, func)

def unescape(string: str) -> str:
    """
    Unescape HTML characters in a string.
    
    Args:
        string: The string to unescape
        
    Returns:
        An unescaped string
    """
    unescape_map = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#x27;": "'",
        "&#x60;": "`",
    }
    for key, value in unescape_map.items():
        string = string.replace(key, value)
    return string

def now() -> int:
    """
    Return the current timestamp in milliseconds.
    
    Returns:
        The current time as milliseconds since epoch
    """
    return int(time.time() * 1000)

def memoize(func: Callable) -> Callable:
    """
    Cache the results of function calls.
    
    Args:
        func: The function to memoize
        
    Returns:
        A memoized version of the function
    """
    cache = {}

    def memoized_func(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    return memoized_func

def random(min_val: int, max_val: int) -> int:
    """
    Return a random integer between min_val and max_val, inclusive.
    
    Args:
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)
        
    Returns:
        A random integer
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
    """
    return lambda: value

def noop() -> None:
    """
    A function that does nothing (no operation).
    
    Returns:
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

def decompress(comp: str) -> str:
    """
    Decompress a given string, which is compressed using run-length encoding.
    
    Args:
        comp: The compressed string to be decompressed
        
    Returns:
        The decompressed string
    """
    result = []
    i = 0

    while i < len(comp):
        # Extract the number (count of characters)
        count = 0
        while i < len(comp) and comp[i].isdigit():
            count = count * 10 + int(comp[i])  # Handle multi-digit counts
            i += 1

        # Extract the character
        if i < len(comp):
            char = comp[i]
            result.append(char * count)  # Append repeated character
            i += 1

    return "".join(result)

def max_value(array: List[T], key_func: Optional[Callable[[T], Any]] = None) -> Optional[T]:
    """
    Return the maximum value in the array, based on an optional key function.
    
    Args:
        array: The array to search
        key_func: Optional function to determine the comparison key
        
    Returns:
        The maximum value or None if array is empty
    """
    if not array:
        return None
    if key_func:
        return max(array, key=key_func)
    return max(array)

def min_value(array: List[T], key_func: Optional[Callable[[T], Any]] = None) -> Optional[T]:
    """
    Return the minimum value in the array, based on an optional key function.
    
    Args:
        array: The array to search
        key_func: Optional function to determine the comparison key
        
    Returns:
        The minimum value or None if array is empty
    """
    if not array:
        return None
    if key_func:
        return min(array, key=key_func)
    return min(array)

def some(array: List[T], func: Callable[[T], bool]) -> bool:
    """
    Check if at least one element in the array matches the predicate.
    
    Args:
        array: The array to check
        func: A predicate function
        
    Returns:
        True if any element matches, False otherwise
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
    """
    return all(func(x) for x in array)

def chain(obj: Any) -> Any:
    """
    Enable chaining by wrapping the object in a chainable class.
    
    Args:
        obj: The object to wrap
        
    Returns:
        A chainable wrapper
    """
    # Import locally to avoid circular imports
    from .core import UniCoreFWWrapper
    return UniCoreFWWrapper(obj)