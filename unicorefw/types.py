"""
File: unicorefw/types.py
Type checking functions for UniCoreFW.

This module contains functions for checking and validating types.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""
import re
import types
import math
from collections.abc import Sequence, Set
from typing import Any, List, Mapping, Tuple

def is_string(obj: Any) -> bool:
    """
    Check if obj is a string.

    Args:
        obj: The object to check

    Returns:
        True if obj is a string, False otherwise

    Examples:
        >>> is_string('hello')
        True
    """
    return isinstance(obj, str)


def is_number(obj: Any) -> bool:
    """
    Check if obj is a number (int or float).

    Args:
        obj: The object to check

    Returns:
        True if obj is a number, False otherwise

    Examples:
        >>> is_number(1)
        True
    """
    return isinstance(obj, (int, float))


def is_array(obj: Any) -> bool:
    """
    Check if obj is a list.

    Args:
        obj: The object to check

    Returns:
        True if obj is a list, False otherwise
    
    Examples:
        >>> is_array([1, 2, 3])
        True
    """
    return isinstance(obj, list)


def is_object(obj: Any) -> bool:
    """
    Check if obj is a dictionary.

    Args:
        obj: The object to check

    Returns:
        True if obj is a dictionary, False otherwise
    
    Examples:
        >>> is_object({'a': 1, 'b': 2})
        True

   """
    return isinstance(obj, dict)


def is_function(obj: Any) -> bool:
    """
    Check if obj is callable (function).

    Args:
        obj: The object to check

    Returns:
        True if obj is callable, False otherwise
    
    Examples:
        >>> is_function(lambda x: x)
        True
    """
    return callable(obj)


def is_boolean(obj: Any) -> bool:
    """
    Check if obj is a boolean.

    Args:
        obj: The object to check

    Returns:
        True if obj is a boolean, False otherwise
    
    Examples:
        >>> is_boolean(True)
        True
    """
    return isinstance(obj, bool)


def is_date(obj: Any) -> bool:
    """
    Check if obj is a date object.

    Args:
        obj: The object to check

    Returns:
        True if obj is a date, False otherwise
    
    Examples:
        >>> is_date(date.today())
        True
    """
    from datetime import date

    return isinstance(obj, date)


def is_reg_exp(obj: Any) -> bool:
    """
    Check if obj is a regular expression.

    Args:
        obj: The object to check

    Returns:
        True if obj is a regular expression, False otherwise
    
    Examples:
        >>> is_reg_exp(re.compile('.*'))
        True
    """
    return isinstance(obj, re.Pattern)


def is_error(obj: Any) -> bool:
    """
    Check if obj is an error instance.

    Args:
        obj: The object to check

    Returns:
        True if obj is an exception, False otherwise
    Examples:
        >>> is_error(Exception())
        True
    """
    return isinstance(obj, Exception)


def is_null(obj: Any) -> bool:
    """
    Check if obj is None.

    Args:
        obj: The object to check

    Returns:
        True if obj is None, False otherwise

    Examples:
        >>> is_null(None)
        True
    """
    return obj is None


def is_undefined(obj: Any) -> bool:
    """
    Check if obj is undefined (None in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is None, False otherwise
    
    Examples:
        >>> is_undefined(None)
        True
    """
    return obj is None


def is_finite(obj: Any) -> bool:
    """
    Check if obj is a finite number.

    Args:
        obj: The object to check

    Returns:
        True if obj is a finite number, False otherwise
    
    Examples:
        >>> is_finite(1)
        True
    """
    return isinstance(obj, (int, float)) and math.isfinite(obj)


def is_nan(obj: Any) -> bool:
    """
    Check if obj is NaN.

    Args:
        obj: The object to check

    Returns:
        True if obj is NaN, False otherwise

    Examples:
        >>> is_nan(float('nan'))
        True
    """
    return isinstance(obj, float) and math.isnan(obj)


def is_map(obj: Any) -> bool:
    """
    Check if obj is a map (dictionary in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is a dictionary, False otherwise

    Examples:
        >>> is_map({'a': 1, 'b': 2})
        True
    """
    return isinstance(obj, dict)


def is_set(obj: Any) -> bool:
    """
    Check if obj is a set.

    Args:
        obj: The object to check

    Returns:
        True if obj is a set, False otherwise

    Examples:
        >>> is_set(set([1, 2, 3]))
        True
    """
    return isinstance(obj, set)


def is_arguments(obj: Any) -> bool:
    """
    Check if obj is an arguments object (tuple in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is a tuple, False otherwise
    
    Examples:
        >>> is_arguments((1, 2, 3))
        True
    """
    return isinstance(obj, tuple)


def is_array_buffer(obj: Any) -> bool:
    """
    Check if obj is an ArrayBuffer (array.array in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is an array.array, False otherwise

    Examples:
        >>> from array import array
        >>> is_array_buffer(array('i', [1, 2, 3]))
        True
    """
    import array

    return isinstance(obj, array.array)


def is_data_view(obj: Any) -> bool:
    """
    Check if obj is a DataView (memoryview in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is a memoryview, False otherwise

    Examples:
        >>> from array import array
        >>> is_data_view(memoryview(array('i', [1, 2, 3])))
        True
    """
    return isinstance(obj, memoryview)


def is_typed_array(obj: Any) -> bool:
    """
    Check if obj is a typed array (array.array in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is an array.array, False otherwise
    
    Examples:
        >>> from array import array
        >>> is_typed_array(array('i', [1, 2, 3]))
        True
    """
    from array import array

    return isinstance(obj, array)


def is_weak_map(obj: Any) -> bool:
    """
    Check if obj is a WeakMap (WeakKeyDictionary in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is a WeakKeyDictionary, False otherwise

    Examples:
        >>> from weakref import WeakKeyDictionary
        >>> is_weak_map(WeakKeyDictionary())
        True
    """
    from weakref import WeakKeyDictionary

    return isinstance(obj, WeakKeyDictionary)


def is_weak_set(obj: Any) -> bool:
    """
    Check if obj is a WeakSet (WeakSet in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is a WeakSet, False otherwise
    
    Examples:
        >>> from weakref import WeakSet
        >>> is_weak_set(WeakSet())
        True
    """
    from weakref import WeakSet

    return isinstance(obj, WeakSet)


def is_element(obj: Any) -> bool:
    """
    Check if obj is a DOM element (ElementTree.Element in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is an Element, False otherwise
    
    Examples:
        >>> from xml.etree.ElementTree import Element
        >>> is_element(Element("foo"))
        True
    """
    try:
        from xml.etree.ElementTree import Element

        return isinstance(obj, Element)
    except ImportError:
        return False


def is_empty(obj: Any) -> bool:
    """
    Check if an object is empty.

    Args:
        obj: The object to check

    Returns:
        True if obj is empty, False otherwise
    
    Examples:
        >>> is_empty([])
        True
        >>> is_empty({})
        True
    """
    # any non-collection primitive (no __len__ and no __iter__) is "empty"
    if not hasattr(obj, "__len__") and not hasattr(obj, "__iter__"):
        return True
    if hasattr(obj, "__len__"):
        return len(obj) == 0
    # objects with __iter__ but no __len__ (e.g. generators)
    return not any(True for _ in obj)

def is_symbol(obj: Any) -> bool:
    """
    Check if an object is a type that could be considered a 'symbol' in Python.

    This includes module types, function types, and unique identifiers.

    Args:
        obj: The object to check

    Returns:
        True if obj is a symbol-like type, False otherwise
    """
    return isinstance(
        obj, (types.ModuleType, types.BuiltinFunctionType, types.FunctionType, type)
    )

def is_equal(obj1: Any, obj2: Any) -> bool:
    """
    Deep equality with cycle handling and fast paths.

    Semantics:
      - Requires exact same type (type(a) is type(b)), like your original.
      - dict/Mapping: keys must match; values compared deeply.
      - list/tuple/Sequence (not str/bytes/bytearray): order matters.
      - set/frozenset/Set: order doesn't matter (direct equality).
      - Other types fall back to ==.
      - No special-casing for NaN (NaN != NaN), preserving original behavior.

    Complexity: O(N) in the total number of elements visited across both structures.

    Args:
        obj1: First object to compare
        obj2: Second object to compare

    Returns:
        True if objects are deeply equal, False otherwise

    Examples:
        >>> is_equal([1, 2, 3], [1, 2, 3])
        True
    """
    if obj1 is obj2:
        return True
    if type(obj1) is not type(obj2):
        return False

    # Fast-path for common immutables
    if isinstance(obj1, (int, float, str, bool, type(None), bytes, bytearray, memoryview, range)):
        return obj1 == obj2

    # Iterative DFS with cycle detection on (id(a), id(b)) pairs
    seen: set[Tuple[int, int]] = set()
    stack: List[Tuple[Any, Any]] = [(obj1, obj2)]

    while stack:
        a, b = stack.pop()
        if a is b:
            continue
        if type(a) is not type(b):
            return False

        pid = (id(a), id(b))
        if pid in seen:
            continue
        seen.add(pid)

        # Re-check fast-path for inner elements
        if isinstance(a, (int, float, str, bool, type(None), bytes, bytearray, memoryview, range)):
            if a != b:
                return False
            continue

        # Mappings: keys must match; push value pairs
        if isinstance(a, Mapping):
            # Quick reject on size or key set mismatch
            if len(a) != len(b):  # type: ignore[arg-type]
                return False
            # Using mapping view equality is O(n) and order-insensitive
            if a.keys() != b.keys():  # type: ignore[arg-type]
                return False
            # Compare corresponding values
            for k in a.keys():
                stack.append((a[k], b[k]))  # type: ignore[index]
            continue

        # Sets (unordered)
        if isinstance(a, Set) and not isinstance(a, (str, bytes, bytearray)):
            # Direct set equality is fine
            if a != b:  # type: ignore[comparison-overlap]
                return False
            continue

        # Sequences (ordered) – but exclude string/bytes-like
        if isinstance(a, Sequence) and not isinstance(a, (str, bytes, bytearray)):
            if len(a) != len(b):  # type: ignore[arg-type]
                return False
            # Push in order so mismatches are caught early
            # (iterate by index to avoid zip generator overhead)
            for i in range(len(a)):  # type: ignore[arg-type]
                stack.append((a[i], b[i]))  # type: ignore[index]
            continue

        # Fallback for everything else (custom objects, etc.)
        if a != b:
            return False

    return True
