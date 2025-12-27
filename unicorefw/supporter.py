"""
File: unicorefw/supporter.py
Supporter functions for UniCoreFW.

This module contains functions for working with dictionaries and object-like structures.


Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""

import ast
from collections import deque
import re
from typing import (
    Any, Callable, Dict, Iterable, List, 
    Optional, Tuple, Union, cast,
    Sequence as TypingSequence
)
import unicodedata

PathKey = Union[str, int, Tuple[Any, ...]]
Path = TypingSequence[PathKey]

def _normalize_customizer(customizer):
    """
    Normalize a customizer function by returning the same function if it is callable,
    returning None if it is None, or returning the type of the customizer if it is a concrete
    object instance (e.g., {} or []).

    Args:
        customizer : Callable or None or object
        The customizer function to normalize.

    Returns:
        Callable or None or type

    Examples:
        >>> _normalize_customizer(lambda x: x)
        <function ...>
        >>> _normalize_customizer(None)
        None
        >>> _normalize_customizer({})
        <class 'dict'>
        >>> _normalize_customizer([])
        <class 'list'>
    """
    if callable(customizer):
        return customizer
    if customizer is None:
        return None
    # If a concrete instance is provided (e.g., {} or []), create empty of same type.
    try:
        typ = type(customizer)
        return typ
    except Exception:
        return None

def _ensure_container(
    parent, key, ctor: Optional[Callable] = None, *, prefer_list_index: bool = False
):
    """
    Ensure parent[key] exists; when absent, create by:
      - ctor() if provided, else [] if prefer_list_index else {}.
    Works for dicts, lists (by index), and objects with attributes.

    Args:
        parent: The parent structure to store the container in.
        key: The key/index to store the container at.
        ctor: The constructor function to call to create the container. If not provided,
            a list or dict is used based on `prefer_list_index`.
        prefer_list_index: Whether to create a list or a dict if no `ctor` is provided.

    Returns:
        A tuple of (container, exists) where container is the created or existing container
        and exists is a boolean indicating whether the container already existed or not.
    
    Examples:
        >>> _ensure_container({}, "key")
        ({}, False)
        >>> _ensure_container([], 0)
        ([], False)
        >>> _ensure_container(MyClass(), "attr")
        (MyClass(), False)
        >>> _ensure_container({}, "key", prefer_list_index=True)
        ([], False)
        >>> _ensure_container([], 0, prefer_list_index=True)
        ([], False)
        >>> _ensure_container(MyClass(), "attr", prefer_list_index=True)
        ([], False)
    """
    container = None
    exists = False
    ctor = _normalize_customizer(ctor)

    if isinstance(parent, dict):
        if key in parent:
            container = parent[key]
            exists = True
        else:
            container = ctor() if ctor else ([] if prefer_list_index else {})
            parent[key] = container

    elif isinstance(parent, list) and isinstance(key, int):
        while key >= len(parent):
            parent.append(None)
        if parent[key] is None:
            parent[key] = ctor() if ctor else ([] if prefer_list_index else {})
        container = parent[key]
        exists = True

    else:
        if hasattr(parent, str(key)):
            container = getattr(parent, str(key))
            exists = True
        else:
            container = ctor() if ctor else ([] if prefer_list_index else {})
            setattr(parent, str(key), container)

    return container, exists
def _is_int_str(s: str) -> bool:
    """Check if a string is a valid integer (e.g. "1", "-2", "+3", etc.)."""
    
    return bool(re.fullmatch(r"-?\d+", s))

def _call_customizer(customizer: Callable, value, key=None, parent=None):
    """
    Call `customizer` with a flexible arity:
      (value, key, parent) → (value, key) → (value)
    Return the custom value if not None; otherwise return None so caller can use default behavior.

    Args:
        customizer: The customizer function to call.
        value: The value to pass to the customizer.
        key: The key to pass to the customizer.
        parent: The parent to pass to the customizer.

    Returns:
        The result of calling `customizer` with the provided arguments.
    
    Examples:
        >>> _call_customizer(lambda x: x, 1)
        1
        >>> _call_customizer(lambda x, y: x + y, 1, 2)
        3
    """
    try:
        return customizer(value, key, parent)
    except TypeError:
        try:
            return customizer(value, key)
        except TypeError:
            return customizer(value)

def _iter_items_like(obj: Any) -> Iterable[Tuple[Any, Any]]:
    """
    Iterate over an object like a dict or sequence, returning (key, value) pairs.

    Args:
        obj: The object to iterate over.

    Yields:
        (key, value) pairs.

    Notes:
        If obj is None, an empty iterator is returned.
        If obj is a dict, the .items() method is called and the result is returned.
        If obj is a sequence (list or tuple), the enumerate() function is called and the result is returned.
        If obj has an .items() method, it is called and the result is returned.
        If obj has an .iteritems() method, it is called and the result is returned.
        If obj has a __dict__ attribute, the .items() method is called on it and the result is returned.
        If obj does not fit any of the above criteria, a single-element iterator is returned with the key set to 0 and the value set to obj.
    
    Examples:
        >>> for k, v in _iter_items_like({"a": 1, "b": 2}):
        ...     print(k, v)
        a 1
        b 2
    """
    if obj is None:
        return iter(())
    if isinstance(obj, dict):
        return iter(obj.items())
    if isinstance(obj, (list, tuple)):
        return iter(enumerate(obj))
    if hasattr(obj, "items") and callable(getattr(obj, "items")):
        return iter(getattr(obj, "items")())
    if hasattr(obj, "iteritems") and callable(getattr(obj, "iteritems")):
        return iter(getattr(obj, "iteritems")())
    if hasattr(obj, "__dict__"):
        return iter(obj.__dict__.items())
    # last resort: single
    return iter([(0, obj)])

def _is_containerish(x: Any) -> bool:
    """
    Return True if x can hold nested fields (dict, list, or any object with attributes), False otherwise.

    Args:
        x: The object to check

    Returns:
        True if x can hold nested fields, False otherwise

    Notes:
        If x is a dict or list, return True.
        If x is a simple immutable (str, bytes, bytearray, bool, int, float, complex, range, tuple), return False.
        If x has a __dict__ attribute, return True. Otherwise, return False.

    Examples:
        >>> _is_containerish({"a": 1})
        True
        >>> _is_containerish([1, 2])
        True
        >>> _is_containerish(1)
        False
        >>> _is_containerish("a")
        False
        >>> _is_containerish({"a": 1}.__dict__)
        True
    """
    if isinstance(x, (dict, list)):
        return True
    # Treat simple immutables as non-containerish
    if isinstance(x, (str, bytes, bytearray, bool, int, float, complex, range, tuple)):
        return False
    return hasattr(x, "__dict__")

def _ensure_len(seq: list, size: int) -> None:
    """
    Ensure the list has at least the given size. If the list is too short, pad it with None.

    Args:
        seq: The list to ensure the length of
        size: The minimum length of the list

    Returns:
        None

    Examples:
        >>> seq = [1, 2]
        >>> _ensure_len(seq, 5)
        >>> seq
        [1, 2, None, None, None]
    """
    missing = size - len(seq)
    if missing > 0:
        seq.extend([None] * missing)

def _parse_path(path: Union[str, int]) -> List[Union[str, int]]:
    """
    Parse a path string or int into a list of path segments.

    A path segment can be a string key or an integer index. The path string
    is parsed as a sequence of segments separated by ".". A segment can also
    be an integer index enclosed in square brackets ("[]").

    For example, the path string "a[1].b" would be parsed as ["a", 1, "b"]

    Args:
        path: The path string or int to parse.

    Returns:
        A list of path segments.

    Examples:
        >>> _parse_path("a.b")
        ["a", "b"]
        >>> _parse_path("a[1]")
        ["a", 1]
        >>> _parse_path("a[1].b")
        ["a", 1, "b"]
    """
    if isinstance(path, int):
        return [path]
    tokens: List[Union[str, int]] = []
    i = 0
    while i < len(path):
        if path[i] == ".":
            i += 1
            continue
        if path[i] == "[":
            j = path.find("]", i)
            idx = int(path[i + 1 : j])
            tokens.append(idx)
            i = j + 1
        else:
            # read until . or [
            j = i
            while j < len(path) and path[j] not in ".[":
                j += 1
            tokens.append(path[i:j])
            i = j
    return tokens

def _get_by_path(obj: Any, path: List[Union[str, int]]) -> Any:
    """
    Safely get a nested value, returning None on any lookup failure.

    Args:
        obj: The object to start the lookup from.
        path: The path to follow to get the value.

    Returns:
        The value at the end of the path, or None if any part of the path
        does not exist.

    Examples:
        >>> _get_by_path({"a": {"b": 1}}, ["a", "b"])
        1
        >>> _get_by_path({"a": {"b": 1}}, ["a", "b", "c"])
        None
    """

    cur = obj
    for seg in path:
        if cur is None:
            return None
        try:
            # try mapping/sequence access first
            cur = cur[seg]  # type: ignore
        except Exception:
            try:
                # fallback to attribute
                cur = getattr(cur, seg)  # type: ignore
            except Exception:
                return None
    return cur

def _set_by_path(
    res: Dict[Any, Any],
    path: Path,
    value: Any,
    original: Any,
) -> None:
    """
    Place `value` into `res` under the same nested structure as in `original`.
    Allow tuple keys (e.g., ('k',)) by typing dict keys as Any.
    Creates dicts or lists as needed. Root is always a dict.

    Args:
        res: The object to place the value into.
        path: The path to follow to place the value.
        value: The value to place.
        original: The object that was used to derive the path.

    Returns:
        None

    Examples:
        >>> _set_by_path({"a": {"b": 1}}, ["a", "b"], 2, {"a": {"b": 1}})
        {"a": {"b": 2}}
    """
    cur: Union[Dict[Any, Any], List[Any]] = res

    for idx, seg in enumerate(path):
        last = idx == len(path) - 1

        if last:
            if isinstance(seg, int):
                if not isinstance(cur, list):
                    raise TypeError("Internal error: expected list container")
                seq = cast(List[Any], cur)
                # while len(seq) <= seg:
                #     seq.append(None)
                _ensure_len(seq, seg + 1)
                seq[seg] = value
            else:
                # seg can be str OR tuple (PathKey excludes int here)
                if not isinstance(cur, dict):
                    raise TypeError("Internal error: expected dict container")
                mp = cast(Dict[Any, Any], cur)
                mp[seg] = value
            return

        nxt = path[idx + 1]

        if isinstance(seg, int):
            # current must be a list
            if not isinstance(cur, list):
                raise TypeError("Internal error: expected list container")
            seq = cast(List[Any], cur)
            _ensure_len(seq, seg + 1)
            
            if seq[seg] is None or not isinstance(seq[seg], (dict, list)):
                # list element becomes list if next is int, else dict
                seq[seg] = [] if isinstance(nxt, int) else {}
            cur = cast(Union[Dict[Any, Any], List[Any]], seq[seg])
        else:
            # current must be a dict
            if not isinstance(cur, dict):
                raise TypeError("Internal error: expected dict container")
            mp = cast(Dict[Any, Any], cur)
            if seg not in mp or not isinstance(mp[seg], (dict, list)):
                # under a dict key, create list only if the NEXT segment is an int
                mp[seg] = [] if isinstance(nxt, int) else {}
            cur = cast(Union[Dict[Any, Any], List[Any]], mp[seg])


def _parse_path_str(s: str) -> List[Union[str, int, tuple]]:
    """Parse a string into a list of path segments.

    This function is used to parse strings into the segments used in the path-related functions.

    The string is split into segments using the following rules:
        - A period (.) separates segments.
        - A bracketed expression ([<expression>]) separates segments.
            - The expression may be a literal (e.g., "(2,)"), an integer (e.g., "2"), or a string.
            - If the expression is a literal or integer, it is parsed as such.
            - If the expression is a string, it is left as is.
        - Any other characters are part of a segment.
    Args:
        s: The string to parse.

    Returns:
        A list of path segments.

    Examples:
        >>> _parse_path_str("a.b[2].c")
        ["a", "b", 2, "c"]
        >>> _parse_path_str("a.b[  2  ].c")
        ["a", "b", 2, "c"]
        >>> _parse_path_str("a.b[ (2,) ].c")
        ["a", "b", (2,), "c"]
        >>> _parse_path_str("a.b[ two ].c")
        ["a", "b", "two", "c"]
    """
    parts: List[Union[str, int, tuple]] = []
    buf: List[str] = []
    i, n = 0, len(s)

    def flush():
        if buf:
            token = "".join(buf)
            parts.append(int(token) if _is_int_str(token) else token)
            buf.clear()

    while i < n:
        ch = s[i]
        if ch == "\\":
            i += 1
            if i < n:
                buf.append(s[i])
        elif ch == ".":
            flush()
        elif ch == "[":
            flush()
            j = i + 1
            bracket: List[str] = []
            while j < n and s[j] != "]":
                bracket.append(s[j])
                j += 1
            token = "".join(bracket).strip()
            if token != "":
                # Try literal (e.g., "(2,)" -> tuple), else int, else raw string
                lit = None
                try:
                    lit = ast.literal_eval(token)
                except Exception:
                    pass
                if lit is not None:
                    parts.append(lit)
                elif _is_int_str(token):
                    parts.append(int(token))
                else:
                    parts.append(token)
            i = j
        else:
            buf.append(ch)
        i += 1
    flush()
    return parts

def _as_parts_any(p: Union[str, List[Union[str, int]], Tuple, Any]) -> List[Union[str, int, tuple]]:
    """
    Converts a given path to a list of path parts.

    Paths can be specified as a string, list of strings/integers, tuple of strings/integers, or any other type.
    If the path is a string, it is tokenized according to the rules of `_parse_path_str`.
    If the path is a tuple, it is wrapped in a list.
    If the path is of any other type, it is wrapped in a list.

    Args:
        p (Union[str, List[Union[str, int]], Tuple, Any]): The path to be converted.

    Returns:
        List[Union[str, int, tuple]]: A list of path parts.

    Examples:
        >>> _as_parts_any("a.b.c")
        ['a', 'b', 'c']
        >>> _as_parts_any(["a", "b", "c"])
        ['a', 'b', 'c']
        >>> _as_parts_any(("a", "b", "c"))
        [('a', 'b', 'c')]
        >>> _as_parts_any(1)
        [1]
    """
    if isinstance(p, list):
        return list(p)
    if isinstance(p, tuple):
        return [p]
    if isinstance(p, str):
        return _parse_path_str(p)
    return [p]


def _flatten(
    array: Any,
    depth: float = float("inf"),
    *,
    expand_types: Tuple[type, ...] = (list, tuple, set),
) -> list:
    """
    Efficiently flatten a nested list structure to the given depth using an iterative approach.

    Time Complexity: O(n) where n is the total number of elements in the flattened result
    Space Complexity: O(d) where d is the maximum depth of nesting

    Args:
        array: A list to flatten (supports nested lists)
        depth: Maximum depth to flatten. Use `True` for shallow (depth=1), float('inf') for full flatten.
        expand_types: Tuple of types that should be expanded during flattening

    Returns:
        Flattened list.

    Examples:
        >>> _flatten([[1], [2, [3]], [[4]]], 2)
        [1, 2, 3, [4]]
    """
    # Increment depth to match original algorithm
    depth += 1
    
    if array is None:
        return []

    if depth is True:
        depth = 2  # True means depth=1, so after +1 it becomes 2
    elif isinstance(depth, (int, float)) and depth < 0:
        return array

    result = []
    
    # Use deque for O(1) operations - this is our main optimization
    stack = deque([(array, depth)])

    while stack:
        current, current_depth = stack.pop()
        
        # Check if current item should be expanded
        if isinstance(current, expand_types) and current_depth > 0:
            # Calculate new depth
            new_depth = current_depth - 1 if current_depth != float("inf") else current_depth
            
            # Add items to stack in reverse order for correct left-to-right processing
            for item in reversed(current):
                stack.append((item, new_depth))
        else:
            result.append(current)

    return result


def _flatten_keys(args) -> List[Any]:
    """
    Flatten a list of arguments, where each argument can be a list/tuple/set of values, into a single list of values.
    
    This function maintains DRY principles by delegating to _flatten with appropriate parameters.

    Time Complexity: O(n) where n is the total number of elements
    Space Complexity: O(n) for the result list

    Args:
        args (Any): A list of arguments to be flattened.

    Returns:
        List[Any]: A flat list of values.

    Examples:
        >>> _flatten_keys([1, [2, 3], 4])
        [1, 2, 3, 4]
        >>> _flatten_keys([1, (2, 3), 4])
        [1, 2, 3, 4]
        >>> _flatten_keys([1, {2, 3}, 4])
        [1, 2, 3, 4]
    """
    # Use depth=1 which becomes depth=2 after the +1 in _flatten
    # This will flatten exactly one level, which is what _flatten_keys needs
    return _flatten(args, depth=1, expand_types=(list, tuple, set))

def _split_apply_args(fn_or_val, *args, **kwargs):
    """
    If first arg isn't callable but the next is, treat as value-first:
      (value, fn, *rest) -> (fn, (value, *rest), kwargs)
    Otherwise:
      (fn, *args) -> (fn, args, kwargs)

    Args:
        fn_or_val: The function or value to apply.
        *args: The arguments to apply the function to.
        **kwargs: The keyword arguments to apply the function with.

    Returns:
        A tuple containing the function to apply, the arguments to apply it to, and the keyword arguments to apply it with.

    Examples:
        >>> _split_apply_args(lambda x, y: x + y, 1, 2)
        (lambda x, y: x + y, (1, 2), {})
        >>> _split_apply_args(1, lambda x, y: x + y, 2)
        (lambda x, y: x + y, (1, 2), {})
    """
    if not callable(fn_or_val) and args and callable(args[0]):
        real_fn = args[0]
        new_args = (fn_or_val, *args[1:])
        return real_fn, new_args, kwargs
    return fn_or_val, args, kwargs  # type: ignore

def _copy_function_metadata(wrapper: Callable, original: Callable) -> Callable:
    """
    DRY helper to copy function metadata consistently across all decorators.
    
    Args:
        wrapper: The wrapper function
        original: The original function
        
    Returns:
        The wrapper function with copied metadata
        
    Examples:
        >>> @_copy_function_metadata
        ... def foo():
        ...     pass
        >>> foo.__name__
        'foo'
    """
    wrapper.__name__ = getattr(original, '__name__', 'anonymous')
    wrapper.__doc__ = getattr(original, '__doc__', None)
    wrapper.__wrapped__ = original # type: ignore
    return wrapper

def _validate_callable(func: Any) -> None:
    """
    Security validation to ensure input is callable.
    
    Args:
        func: Object to validate
        
    Raises:
        TypeError: If func is not callable
    
    Examples:
        >>> _validate_callable(lambda x: x)
        >>> _validate_callable(1)
        Traceback (most recent call last):
        ...
        TypeError: Expected callable, got int
    """
    if not callable(func):
        raise TypeError(f"Expected callable, got {type(func).__name__}")


def _to_str(s: Any) -> str:
    """Internal helper: coerce to string, treating None as empty."""
    return "" if s is None else str(s)


def _parse_js_regex(literal: str) -> (str, int, bool): # type: ignore
    """
    Parse a JS-style regex literal into a body string, flags, and a global flag.

    Args:
        literal: The string to parse.

    Returns:
        A tuple of (body, flags, is_global) where:
            - body is the regex pattern string.
            - flags is a bitfield of re.IGNORECASE, re.MULTILINE, and re.DOTALL.
            - is_global is True if the regex has the 'g' flag, False otherwise.

    Examples:
        >>> _parse_js_regex("/abc/i")
        ("abc", re.IGNORECASE, False)
    """
    if not isinstance(literal, str) or len(literal) < 2 or literal[0] != '/':
        return literal, 0, False
    # find trailing slash
    idx = literal.rfind('/')
    if idx == 0:
        # no closing slash
        return literal, 0, False
    body = literal[1:idx]
    flags_str = literal[idx+1:]
    flags = 0
    global_flag = False
    for ch in flags_str:
        if ch == 'i':
            flags |= re.IGNORECASE
        elif ch == 'm':
            flags |= re.MULTILINE
        elif ch == 's':
            flags |= re.DOTALL
        elif ch == 'g':
            global_flag = True
    return body, flags, global_flag

def _deburr_latin_only(text: str) -> str:
    """
    Remove diacritical marks from Latin characters in the given text.

    This function is similar to :func:`unicodedata.normalize("NFD", text)`, but it
    only applies to Latin characters, leaving other Unicode characters
    unchanged. This is useful for text normalization when you don't want to
    convert all of the Unicode characters, but only the Latin ones.

    Args:
        text: The text to deburr.

    Returns:
        The deburred text.

    Examples:
        >>> _deburr_latin_only("déjà vu")
        "deja vu"
        >>> _deburr_latin_only("\xc0\xc1\xc6\xdf")
        "AAAEss"    
    """
    out = []
    for ch in text:
        name = unicodedata.name(ch, "")
        if "LATIN" in name:
            decomp = unicodedata.normalize("NFD", ch)
            decomp = "".join(c for c in decomp if unicodedata.category(c) != "Mn")
            out.append(decomp)
        else:
            out.append(ch)
    return "".join(out)


def _try_import(module_name: str) -> Optional[Any]:
    """
    Safely attempt to import a module.
    
    Args:
        module_name: The name of the module to import.
        
    Returns:
        The imported module if successful, None otherwise

    Examples:
        >>> _try_import("unicorefw")
        <module 'unicorefw.core' from '/path/to/unicorefw/core.py'>
    """
    try:
        import importlib
        return importlib.import_module(module_name)
    except (ImportError, Exception):
        return None


def _try_asyncio_schedule(asyncio: Any, func: Callable, args: tuple, kwargs: dict) -> bool:
    """
    Try to schedule function execution via asyncio loop.
    
    Args:
        asyncio: The asyncio module
        func: The function to schedule
        args: The arguments to pass to the function
        kwargs: The keyword arguments to pass to the function

    Returns:
        True if successful, False otherwise
    
    Examples:
        >>> _try_asyncio_schedule(asyncio, lambda x: x, (1,), {})
        True
    """
    try:
        loop = asyncio.get_running_loop()
        loop.call_soon_threadsafe(func, *args, **kwargs)
        return True
    except (RuntimeError, AttributeError):
        return False
