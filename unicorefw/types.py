"""
Type checking functions for UniCoreFW.

This module contains functions for checking and validating types.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info
"""

import re
import types
from typing import Any
import math


def is_string(obj: Any) -> bool:
    """
    Check if obj is a string.

    Args:
        obj: The object to check

    Returns:
        True if obj is a string, False otherwise
    """
    return isinstance(obj, str)


def is_number(obj: Any) -> bool:
    """
    Check if obj is a number (int or float).

    Args:
        obj: The object to check

    Returns:
        True if obj is a number, False otherwise
    """
    return isinstance(obj, (int, float))


def is_array(obj: Any) -> bool:
    """
    Check if obj is a list.

    Args:
        obj: The object to check

    Returns:
        True if obj is a list, False otherwise
    """
    return isinstance(obj, list)


def is_object(obj: Any) -> bool:
    """
    Check if obj is a dictionary.

    Args:
        obj: The object to check

    Returns:
        True if obj is a dictionary, False otherwise
    """
    return isinstance(obj, dict)


def is_function(obj: Any) -> bool:
    """
    Check if obj is callable (function).

    Args:
        obj: The object to check

    Returns:
        True if obj is callable, False otherwise
    """
    return callable(obj)


def is_boolean(obj: Any) -> bool:
    """
    Check if obj is a boolean.

    Args:
        obj: The object to check

    Returns:
        True if obj is a boolean, False otherwise
    """
    return isinstance(obj, bool)


def is_date(obj: Any) -> bool:
    """
    Check if obj is a date object.

    Args:
        obj: The object to check

    Returns:
        True if obj is a date, False otherwise
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
    """
    return isinstance(obj, re.Pattern)


def is_error(obj: Any) -> bool:
    """
    Check if obj is an error instance.

    Args:
        obj: The object to check

    Returns:
        True if obj is an exception, False otherwise
    """
    return isinstance(obj, Exception)


def is_null(obj: Any) -> bool:
    """
    Check if obj is None.

    Args:
        obj: The object to check

    Returns:
        True if obj is None, False otherwise
    """
    return obj is None


def is_undefined(obj: Any) -> bool:
    """
    Check if obj is undefined (None in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is None, False otherwise
    """
    return obj is None


def is_finite(obj: Any) -> bool:
    """
    Check if obj is a finite number.

    Args:
        obj: The object to check

    Returns:
        True if obj is a finite number, False otherwise
    """
    return isinstance(obj, (int, float)) and math.isfinite(obj)


def is_nan(obj: Any) -> bool:
    """
    Check if obj is NaN.

    Args:
        obj: The object to check

    Returns:
        True if obj is NaN, False otherwise
    """
    return isinstance(obj, float) and math.isnan(obj)


def is_map(obj: Any) -> bool:
    """
    Check if obj is a map (dictionary in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is a dictionary, False otherwise
    """
    return isinstance(obj, dict)


def is_set(obj: Any) -> bool:
    """
    Check if obj is a set.

    Args:
        obj: The object to check

    Returns:
        True if obj is a set, False otherwise
    """
    return isinstance(obj, set)


def is_arguments(obj: Any) -> bool:
    """
    Check if obj is an arguments object (tuple in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is a tuple, False otherwise
    """
    return isinstance(obj, tuple)


def is_array_buffer(obj: Any) -> bool:
    """
    Check if obj is an ArrayBuffer (array.array in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is an array.array, False otherwise
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
    """
    return isinstance(obj, memoryview)


def is_typed_array(obj: Any) -> bool:
    """
    Check if obj is a typed array (array.array in Python).

    Args:
        obj: The object to check

    Returns:
        True if obj is an array.array, False otherwise
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
    """
    if obj is None:
        return True
    if hasattr(obj, "__len__"):
        return len(obj) == 0
    if hasattr(obj, "__iter__"):
        return not any(True for _ in obj)
    return False


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
    Perform a deep comparison between two objects for equality.

    Args:
        obj1: First object to compare
        obj2: Second object to compare

    Returns:
        True if objects are deeply equal, False otherwise
    """
    if type(obj1) != type(obj2):
        return False
    if isinstance(obj1, dict):
        if len(obj1) != len(obj2):
            return False
        return all(k in obj2 and is_equal(v, obj2[k]) for k, v in obj1.items())
    elif isinstance(obj1, list):
        if len(obj1) != len(obj2):
            return False
        return all(is_equal(x, y) for x, y in zip(obj1, obj2))
    return obj1 == obj2
