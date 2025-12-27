"""
File: unicorefw/object.py
Object manipulation functions for UniCoreFW.

This module contains functions for working with dictionaries and object-like structures.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""
from typing import (
    Any, Callable, Dict, Iterable, List, 
    Mapping, MutableMapping, Optional, 
    Tuple, TypeVar, Union
)
from .supporter import (
    _ensure_container,
    _flatten_keys, 
    _iter_items_like,
    _is_int_str,
    _call_customizer,
    _is_containerish,
    _ensure_len,
    _as_parts_any,
    _parse_path,
    _set_by_path,
    _split_apply_args,
    # _normalize_customizer,
    # _parse_path_str
)
import math
import re
import random
import inspect
import builtins

# runtime ABC (for isinstance checks)
from collections.abc import Sequence as AbcSequence
_RESTRICTED = {"__globals__", "__builtins__"}  # keep restriction *narrow*
_MISSING = builtins.object()

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")
U = TypeVar("U")


def invoke(obj: Any, path: Union[str, List[Union[str, int]]], *args, **kwargs) -> Any:
    """
    - If `obj` is NOT a sequence: resolve `path` on `obj` and call the final method → scalar.
    - If `obj` IS a list/tuple *and* the first segment isn't an int index: apply the same
      resolution per element and return a list of results (including None where it fails).

    Args:
        obj (Any): The object to resolve the path on.
        path (Union[str, List[Union[str, int]]]): The path to resolve.
        *args: Positional arguments to pass to the resolved method.
        **kwargs: Keyword arguments to pass to the resolved method.

    Returns:
        Any: The result of the resolved method, or None if the path is invalid or the method is not callable.   
    
    Examples:
        >>> invoke({"a": {"b": [None, lambda x: x]}}, "a.b.1", 1)
        1
    """
    parts = _as_parts_any(path)
    if not parts:
        return None

    def _invoke_one(root: Any) -> Any:
        parent = root
        for seg in parts[:-1]:
            if parent is None:
                return None
            if isinstance(parent, dict):
                if seg in parent:
                    parent = parent[seg]
                elif isinstance(seg, str) and seg.lstrip("-").isdigit() and (int(seg) in parent):
                    parent = parent[int(seg)]
                elif isinstance(seg, int) and (str(seg) in parent):
                    parent = parent[str(seg)]
                else:
                    return None
            elif isinstance(parent, list) and isinstance(seg, int):
                if -len(parent) <= seg < len(parent):
                    parent = parent[seg]
                else:
                    return None
            else:
                parent = getattr(parent, str(seg), None)
        last = parts[-1]
        if not isinstance(last, str):
            return None
        fn = getattr(parent, last, None)
        if not callable(fn):
            return None
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None

    # Map-style: top-level list/tuple AND path doesn't start with an explicit index
    if isinstance(obj, (list, tuple)) and not (isinstance(parts[0], int)):
        return [_invoke_one(el) for el in obj]

    # Scalar path resolution
    return _invoke_one(obj)


def iterator(obj):
    """
    Yield (key, value) pairs from mappings, sequences, or objects that expose items/iteritems/attributes.
    
    Args:
        obj: The object to iterate

    Returns:
        A generator that yields (key, value) pairs

    Examples:
        >>> list(iterator({"a": 1, "b": 2}))
        [("a", 1), ("b", 2)]
    """
    return _iter_items_like(obj)

def extend(obj: Dict[K, V], *sources: Dict) -> Dict[K, V]:
    """
    Extend obj by copying properties from sources.

    Args:
        obj: The dictionary to extend
        *sources: Dictionaries to copy properties from

    Returns:
        The extended dictionary
    
    Examples:
        >>> extend({"a": 1}, {"b": 2})
        {"a": 1, "b": 2}
    """
    for source in sources:
        obj.update(source)
    return obj

def has(collection: Any, path: Any) -> bool:
    """
    Return True if `path` exists in `collection` (dict, list/tuple/sequence, object).
    Path may be a dotted/bracket string ("a.b[0].c"), a list of segments, an int, etc.

    Args:
        collection (Any): The object to resolve the path on.
        path (Any): The path to resolve.

    Returns:
        bool: True if the path exists, False otherwise.
    
    Examples:
        >>> has({"a": {"b": [None, lambda x: x]}}, "a.b.1")
        True
    """
    parts = _as_parts_any(path)
    if not parts:
        return False

    def _is_inty_str(s: str) -> bool:
        return s.isdigit() or (s.startswith("-") and s[1:].isdigit())

    cur = collection
    for seg in parts:
        # ---- dict lookup (no defaultdict side-effects)
        if isinstance(cur, dict):
            if seg in cur:
                cur = cur[seg]
                continue
            # string<->int coercion
            if isinstance(seg, str) and _is_inty_str(seg) and (i := int(seg)) in cur:
                cur = cur[i]
                continue
            if isinstance(seg, int) and str(seg) in cur:
                cur = cur[str(seg)]
                continue
            return False

        # ---- list (strict int indexing with negatives)
        if isinstance(cur, list):
            if isinstance(seg, int) or (isinstance(seg, str) and _is_inty_str(seg)):
                idx = seg if isinstance(seg, int) else int(seg)
                if idx < 0:
                    idx += len(cur)
                if 0 <= idx < len(cur):
                    cur = cur[idx]
                    continue
            return False

        # ---- namedtuple: allow field-name access or index
        if isinstance(cur, tuple) and hasattr(cur, "_fields"):
            if isinstance(seg, str) and seg in getattr(cur, "_fields", ()):
                cur = getattr(cur, seg)
                continue
            if isinstance(seg, int) or (isinstance(seg, str) and _is_inty_str(seg)):
                idx = seg if isinstance(seg, int) else int(seg)
                if idx < 0:
                    idx += len(cur)
                if 0 <= idx < len(cur):
                    cur = cur[idx]
                    continue
            return False

        # ---- generic sequences (but not strings/bytes)
        if isinstance(cur, AbcSequence) and not isinstance(cur, (str, bytes, bytearray)):
            if isinstance(seg, int) or (isinstance(seg, str) and _is_inty_str(seg)):
                idx = seg if isinstance(seg, int) else int(seg)
                L = len(cur)
                if idx < 0:
                    idx += L
                if 0 <= idx < L:
                    cur = cur[idx]
                    continue
            return False

        # ---- object attribute
        attr = getattr(cur, str(seg), _MISSING)
        if attr is _MISSING:
            return False
        cur = attr

    return True

def defaults(
    obj: MutableMapping[K, V],
    *defaults_dicts: Union[Mapping[K, V], Iterable[Tuple[K, V]]]
) -> MutableMapping[K, V]:
    """
    Fill missing keys on `obj` from one or more defaults sources (left→right).
    Mutates and returns `obj`.

    Args:
        obj (MutableMapping): The object to fill.
        *defaults_dicts (Union[Mapping, Iterable[Tuple]]): The defaults to use.

    Returns:
        MutableMapping

    Examples:
        >>> defaults({"a": 1}, {"a": 0, "b": 2})
        {"a": 1, "b": 2}
    """
    if not isinstance(obj, MutableMapping):
        raise TypeError("The 'obj' parameter must be a mutable mapping.")

    for default in defaults_dicts:
        if default is None:
            continue

        # Normalize to an items() iterator
        if hasattr(default, "items"):  # Mapping-like
            items = default.items()  # type: ignore[assignment]
        else:
            try:
                items = dict(default).items()  # supports iterable of pairs
            except Exception as e:
                raise TypeError(
                    "Each default must be a mapping or iterable of (key, value) pairs."
                ) from e

        # Set only if missing in obj
        for k, v in items:
            if k not in obj:
                obj[k] = v

    return obj

def create(proto: Dict) -> Dict:
    """
    Create an object that inherits from the given prototype (dictionary).

    Args:
        proto: The prototype dictionary

    Returns:
        A new dictionary with prototype properties

    Raises:
        TypeError: If proto is not a dictionary
    
    Examples:
        >>> create({"a": 1})
        {"a": 1}
    """
    if not isinstance(proto, dict):
        raise TypeError("Prototype must be a dictionary")

    class Obj(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.update(proto)

    return Obj()


def pairs(obj: Dict[K, V]) -> List[Tuple[K, V]]:
    """
    Convert an object into an array of [key, value] pairs.

    Args:
        obj: The dictionary to convert

    Returns:
        A list of key-value tuples
    
    Examples:
        >>> pairs({"a": 1, "b": 2})
        [("a", 1), ("b", 2)]
    """
    return list(obj.items())


def result(obj: Dict, property_name: str, *args) -> Any:
    """
    If the property is a function, invoke it with args; otherwise, return the property value.

    Args:
        obj: The dictionary to get the property from
        property_name: The property name to get
        *args: Arguments to pass if the property is a function

    Returns:
        The property value or function result

    Examples:
        >>> result({"a": lambda x: x + 1}, "a", 1)
        2
    """
    value = obj.get(property_name)

    if callable(value):
        # Directly call the function with args if it's callable
        return value(*args)

    return value


def size(obj: Union[Dict, List, Any]) -> int:
    """
    Return the number of values in obj (works for dicts, lists, etc.).

    Args:
        obj: The object to get the size of

    Returns:
        The number of elements/properties

    Examples:
        >>> size({"a": 1, "b": 2})
        2
    """
    if hasattr(obj, "__len__"):
        return len(obj)
    return sum(1 for _ in obj)


def to_array(obj: Union[Dict, List, Any]) -> List:
    """
    Convert obj into an array (list in Python).

    Args:
        obj: The object to convert

    Returns:
        A list representation of the object

    Examples:
        >>> to_array({"a": 1, "b": 2})
        [1, 2]
    """
    if isinstance(obj, list):
        return obj
    elif isinstance(obj, (dict, set)):
        return list(obj.values()) if isinstance(obj, dict) else list(obj)
    elif hasattr(obj, "__iter__"):
        return list(obj)
    return [obj]


def where(obj_list: List[Dict], properties: Dict) -> List[Dict]:
    """
    Return an array of all objects in obj_list that match the key-value pairs in properties.

    Args:
        obj_list: The list of objects to filter
        properties: Key-value pairs to match

    Returns:
        A list of matching objects

    Examples:
        >>> where([{"a": 1, "b": 2}, {"a": 3, "b": 4}], {"a": 1})
        [{"a": 1, "b": 2}]
    """
    return [
        obj for obj in obj_list if all(obj.get(k) == v for k, v in properties.items())
    ]


def object(keys: List[K], values: List[V]) -> Dict[K, V]:
    """
    Create an object (dictionary) from the given keys and values.

    Args:
        keys: The list of keys
        values: The list of values

    Returns:
        A dictionary with the given keys and values

    Raises:
        ValueError: If keys and values don't have the same length
    
    Examples:
        >>> object(["a", "b"], [1, 2])
        {"a": 1, "b": 2}
    """
    if len(keys) != len(values):
        raise ValueError("Keys and values must have the same length")
    return {keys[i]: values[i] for i in range(len(keys))}


def map_object(obj: Dict[K, V], func: Callable[[V], U]) -> Dict[K, U]:
    """
    Apply func to each value in obj, returning a new object with the transformed values.

    Args:
        obj: The dictionary to transform
        func: A function to apply to each value

    Returns:
        A new dictionary with transformed values

    Examples:
        >>> map_object({"a": 1, "b": 2}, lambda x: x + 1)
        {"a": 2, "b": 3}
    """
    return {k: func(v) for k, v in obj.items()}


def all_keys(obj: Dict) -> List:
    """
    Return all the keys of a dictionary, including inherited ones.

    Args:
        obj: The dictionary to get keys from

    Returns:
        A list of keys

    Raises:
        TypeError: If obj is not a dictionary

    Examples:
        >>> all_keys({"a": 1, "b": 2})
        ["a", "b"]
    """
    if isinstance(obj, dict):
        return list(obj.keys())
    else:
        raise TypeError("The input must be a dictionary.")


def is_match(obj: Dict, attrs: Dict) -> bool:
    """
    Check if obj has key-value pairs that match attrs.

    Args:
        obj: The dictionary to check
        attrs: The key-value pairs to match

    Returns:
        True if all key-value pairs match, False otherwise

    Examples:
        >>> is_match({"a": 1, "b": 2}, {"a": 1, "b": 2})
        True
    """
    return all(obj.get(k) == v for k, v in attrs.items())


def functions(obj: Dict) -> List[str]:
    """
    Return the names of all explicitly defined functions in an object (dictionary).

    Args:
        obj: The dictionary to check for functions

    Returns:
        A list of function names defined in the object

    Raises:
        TypeError: If obj is not a dictionary
    
    Examples:
        >>> functions({"a": 1, "b": lambda x: x + 1})
        ["b"]
    """
    if not isinstance(obj, dict):
        raise TypeError("Input must be a dictionary.")

    return [
        key
        for key, value in obj.items()
        if callable(value) and not key.startswith("__")
    ]


def deep_copy(obj: Any) -> Any:
    """
    Create a deep copy of the given object without using imports.

    Args:
        obj: The object to copy

    Returns:
        A deep copy of the object
    Examples:
        >>> deep_copy({"a": 1, "b": 2})
        {"a": 1, "b": 2}
    """
    if isinstance(obj, dict):
        return {k: deep_copy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_copy(elem) for elem in obj]
    elif isinstance(obj, tuple):
        return tuple(deep_copy(elem) for elem in obj)
    elif isinstance(obj, str):
        # Strings are immutable, return as is
        return obj
    else:
        # For immutable objects like int, float, return as is
        return obj

####################################################################################
#  Extended Object Functions
####################################################################################
def at(obj: Dict[Any, Any], *paths: str) -> List[Any]:
    """
    Retrieves the value at the given path of the object.

    The path value can be a string or an array of strings or integers.
    If a path value is an array, it will be used to traverse an array-liked object.

    Args:
        obj: The object to retrieve values from.
        *paths: The path(s) to retrieve values from.

    Returns:
        A list of values at the given paths.

    Examples:
        >>> at({'a': {'b': 2}}, 'a.b')
        [2]
    """
    results: List[Any] = []
    for path in paths:
        current = obj
        # split on dots and brackets
        parts = re.findall(r"[^.\[\]]+", path)
        for p in parts:
            if isinstance(current, dict):
                current = current.get(p)
            elif isinstance(current, (list, tuple)):
                try:
                    idx = int(p)
                    current = current[idx]
                except Exception:
                    current = None
            else:
                current = None
            if current is None:
                break
        results.append(current)
    return results


def filter_(
    collection: Union[Dict[Any, Any], List[Any]],
    predicate: Optional[Callable[[Any], bool]] = None,
) -> List[Any]:
    """
    Filters elements of a collection based on a predicate function.

    Args:
        collection: The dictionary or list to filter.
        predicate: An optional function that returns True for elements to include.
                   If not provided, the truthiness of the element itself is used.

    Returns:
        A list containing elements that satisfy the predicate or are truthy by default.

    Examples:
        >>> filter_({'a': 1, 'b': 2, 'c': 3}, lambda x: x > 1)
        [2, 3]
    """

    pred = predicate or (lambda x: bool(x))
    items = list(collection.values()) if isinstance(collection, dict) else collection
    return [v for v in items if pred(v)]


def find_last(
    collection: Union[Dict[Any, Any], List[Any]],
    predicate: Optional[Callable[[Any], bool]] = None,
) -> Any:
    """
    Finds the last element in a collection that satisfies the predicate.

    Args:
        collection: The dictionary or list to search.
        predicate: An optional function that returns True for elements to include.
                   If not provided, the truthiness of the element itself is used.

    Returns:
        The last element that satisfies the predicate, or None if not found.

    Examples:
        >>> find_last({'a': 1, 'b': 2, 'c': 3}, lambda x: x > 1)
        3
    """
    pred = predicate or (lambda x: bool(x))
    items = list(collection.values()) if isinstance(collection, dict) else collection
    for v in reversed(items):
        if pred(v):
            return v
    return None


def flat_map(collection: List[Any], func: Callable[[Any], List[Any]]) -> List[Any]:
    """
    Creates a flattened list of values by running each element in collection through `func` and
    flattening the mapped results.

    Args:
        collection: Collection to iterate over.
        func: Iteratee applied per iteration.

    Returns:
        Flattened mapped list.

    Examples:
        >>> duplicate = lambda n: [[n, n]]
        >>> flat_map([1, 2], duplicate)
        [[1, 1], [2, 2]]
    """
    result: List[Any] = []
    for x in collection:
        res = func(x)
        if isinstance(res, (list, tuple)):
            result.extend(res)
    return result


def flat_map_deep(collection: List[Any], func: Callable[[Any], List[Any]]) -> List[Any]:
    """
    Recursively flat maps a given collection. This is similar to :func:`flat_map`, but
    will continue to flatten the mapped results until they are no longer iterable.

    Args:
        collection: Collection to iterate over.
        func: Iteratee applied per iteration.

    Returns:
        Fully flattened mapped list.

    Examples:
        >>> nested = lambda x: [[x, x], [x, x]]
        >>> flat_map_deep([1, 2], nested)
        [1, 1, 1, 1, 2, 2, 2, 2]
    """

    def _deep(arr):
        out: List[Any] = []
        for y in arr:
            if isinstance(y, (list, tuple)):
                out.extend(_deep(y))
            else:
                out.append(y)
        return out

    return _deep(flat_map(collection, func))


def flat_map_depth(
    collection: List[Any], func: Callable[[Any], List[Any]], depth: int
) -> List[Any]:
    """
    Recursively flat maps a given collection up to the given depth. This is similar
    to :func:`flat_map`, but will continue to flatten the mapped results until they
    are no longer iterable up to the given depth.

    Args:
        collection: Collection to iterate over.
        func: Iteratee applied per iteration.
        depth: Maximum recursion depth.

    Returns:
        Fully flattened mapped list up to the given depth.

    Examples:
        >>> nested = lambda x: [[x, x], [x, x]]
        >>> flat_map_depth([1, 2], nested, 2)
        [1, 1, 1, 1, 2, 2, 2, 2]
    """
    result = flat_map(collection, func)

    def _flatten(arr: Any, d: int) -> List[Any]:
        """
        Recursively flattens a list or tuple up to the given depth.

        Args:
            arr: The list or tuple to flatten.
            d: The maximum recursion depth.

        Returns:
            A flattened list of elements.

        Examples:
            >>> _flatten([1, 2], 2)
            [1, 1, 1, 1, 2, 2, 2, 2]
        """
        if d <= 0 or not isinstance(arr, (list, tuple)):
            return [arr]
        out: List[Any] = []
        for y in arr:
            if isinstance(y, (list, tuple)):
                out.extend(_flatten(y, d - 1))
            else:
                out.append(y)
        return out

    return _flatten(result, depth)


def for_each(
    collection: Union[Dict[Any, Any], List[Any]], func: Callable[[Any], None]
) -> Union[Dict[Any, Any], List[Any]]:
    """
    Iterates over elements of collection and invokes iteratee for each element.
    The iteratee is invoked with three arguments: (value, index|key, collection).
    Each invocation of iteratee is called for its side-effects upon the collection.
    Collection may be either an object or an array.
    Iteration is stopped if predicate returns Falsey value.
    The predicate is bound to thisArg and invoked with three arguments: (value, index|key, collection).

    Args:
        collection: The collection to iterate over.
        func: The function invoked per iteration.

    Returns:
        The collection.

    Examples:
        >>> for_each([1, 2, 3], lambda x: print(x))
        1
        2
        3
    """
    if isinstance(collection, dict):
        for v in collection.values():
            func(v)  # noqa: E701
    else:
        for v in collection:
            func(v)  # noqa: E701
    return collection


def for_each_right(
    collection: Union[Dict[Any, Any], List[Any]], func: Callable[[Any], None]
) -> Union[Dict[Any, Any], List[Any]]:
    """
    Iterates over elements of a collection from right to left and invokes a function for each element.
    The function is invoked with one argument: the current element.

    Args:
        collection: The collection to iterate over. Can be a dictionary or a list.
        func: The function to invoke for each element. It should accept a single argument.

    Returns:
        The original collection.

    Examples:
        >>> for_each_right([1, 2, 3], lambda x: print(x))
        3
        2
        1
    """

    items = (
        list(collection.values()) if isinstance(collection, dict) else list(collection)
    )
    for v in reversed(items):
        func(v)  # noqa: E701
    return collection


def includes(collection: Union[Dict[Any, Any], List[Any]], value: Any) -> bool:
    """
    Checks if a given value is present in a collection.

    Args:
        collection: The collection to search in. Can be a dictionary or a list.
        value: The value to search for.

    Returns:
        Whether the value is present in the collection.

    Examples:
        >>> includes([1, 2, 3], 2)
        True
    """
    if isinstance(collection, dict):
        return value in collection.values()
    return value in collection


def invoke_map(
    collection: List[Any], method: Union[str, Callable], *args, **kwargs
) -> List[Any]:
    """
    Invokes the given iteratee function on each element of the given collection
    and returns an array of the results. The iteratee is invoked with the
    elements of the collection as the first argument and any additional
    arguments provided to invoke_map as additional arguments.

    Args:
        collection: The collection to process. Should be a list.
        method: The function to invoke on each element. Can be a string
            (in which case getattr is used to get the method from the
            element) or a callable.
        *args: Additional arguments to pass to the iteratee.
        **kwargs: Additional keyword arguments to pass to the iteratee.

    Returns:
        A list of the results of invoking the iteratee on each element of the
        collection.

    Examples:
        >>> invoke_map([1, 2, 3], lambda x: x * 2)
        [2, 4, 6]
    """
    result: List[Any] = []
    for x in collection:
        if isinstance(method, str):
            fn = getattr(x, method)
            result.append(fn(*args, **kwargs))
        else:
            result.append(method(x, *args, **kwargs))
    return result


def key_by(
    collection: List[Dict[Any, Any]], iteratee: Union[str, Callable]
) -> Dict[Any, Dict[Any, Any]]:
    """
    Creates an object composed of keys generated from the results of running each element of the given collection
    through the given iteratee.

    Args:
        collection: The collection to process. Should be a list of dictionaries.
        iteratee: The function to run each element of the collection through. Can be a string
            (in which case the value of the given key is used) or a callable.

    Returns:
        An object with the results of running the iteratee on each element of the collection as keys,
        and the element of the collection as the values.

    Examples:
        >>> key_by([{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], 'a')
        {1: {'a': 1, 'b': 2}, 3: {'a': 3, 'b': 4}}
    """
    if isinstance(iteratee, str):

        def fn(x):
            return x.get(iteratee)
    else:
        fn = iteratee
    out: Dict[Any, Any] = {}
    for x in collection:
        out[fn(x)] = x
    return out


def map_(
    collection: Union[Dict[Any, Any], List[Any]], iteratee: Union[str, Callable]
) -> List[Any]:
    """
    Creates a list of values by running each element of the given collection
    through the given iteratee.

    Args:
        collection: The collection to process. Can be a dictionary or a list.
        iteratee: The function to run each element of the collection through.
            Can be a string (in which case the value of the given key is used)
            or a callable.

    Returns:
        A list of the results of running the iteratee on each element of the
        collection.

    Examples:
        >>> map_([{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], 'a')
        [1, 3]
    """
    if isinstance(iteratee, str):

        def fn(x):
            return x.get(iteratee)
    else:
        fn = iteratee
    items = collection.values() if isinstance(collection, dict) else collection
    return [fn(v) for v in items]


def nest(collection: List[Dict[Any, Any]], keys: List[str]) -> Dict[Any, Any]:
    """
    Groups a list of dictionaries into a nested dictionary based on the specified keys.

    Args:
        collection: A list of dictionaries to be nested.
        keys: A list of keys to nest the dictionaries by. The order of keys
              determines the hierarchy of the nesting.

    Returns:
        A nested dictionary where each level corresponds to a key in the keys
        list, and the final level contains lists of dictionaries from the
        collection that share the same key values.

    Examples:
        >>> collection = [
        ...     {'type': 'fruit', 'name': 'apple', 'color': 'red'},
        ...     {'type': 'fruit', 'name': 'banana', 'color': 'yellow'},
        ...     {'type': 'vegetable', 'name': 'carrot', 'color': 'orange'}
        ... ]
        >>> keys = ['type', 'color']
        >>> nest(collection, keys)
        {
            'fruit': {
                'red': [{'type': 'fruit', 'name': 'apple', 'color': 'red'}],
                'yellow': [{'type': 'fruit', 'name': 'banana', 'color': 'yellow'}],
            },
            'vegetable': {
                'orange': [{'type': 'vegetable', 'name': 'carrot', 'color': 'orange'}]
            }
        }
    """

    out: Dict[Any, Any] = {}
    for x in collection:
        curr = out
        for i, k in enumerate(keys):
            val = x.get(k)
            if i == len(keys) - 1:
                curr.setdefault(val, []).append(x)
            else:
                curr = curr.setdefault(val, {})
    return out


def order_by(
    collection: List[Dict[Any, Any]],
    iteratees: List[Union[str, Callable]],
    orders: Optional[List[str]] = None,
) -> List[Dict[Any, Any]]:
    """
    Orders a collection of dictionaries based on the specified iteratees and their corresponding orders.

    Args:
        collection: The list of dictionaries to be ordered.
        iteratees: A list of iteratees to sort by. Each iteratee can be a string representing
                   a key in the dictionaries or a callable that extracts a value from each element.
        orders: An optional list of sort orders corresponding to each iteratee. Each order can be
                'asc' for ascending or 'desc' for descending. If not provided, all iteratees will
                default to 'asc'.

    Returns:
        A new list of dictionaries sorted according to the specified iteratees and orders.

    Examples:
        >>> items = [{'a': 2, 'b': 3}, {'a': 1, 'b': 4}]
        >>> order_by(items, ['a'], ['asc'])
        [{'a': 1, 'b': 4}, {'a': 2, 'b': 3}]
    """

    result = list(collection)
    orders = orders or ["asc"] * len(iteratees)
    for key_fn, order in reversed(list(zip(iteratees, orders))):
        if isinstance(key_fn, str):

            def fn(x, field=key_fn):
                return x.get(field)
        else:
            fn = key_fn
        result.sort(key=fn, reverse=(order == "desc"))
    return result


def reduce_(
    collection: Union[Dict[Any, Any], List[Any]], func: Callable, initial: Any
) -> Any:
    """
    Reduces a collection to a single accumulated value by applying a function.

    Args:
        collection: The collection to reduce, can be a dictionary or a list.
        func: A function that takes two arguments, the accumulator and the current value, and returns an updated accumulator.
        initial: The initial value for the accumulator.

    Returns:
        The final accumulated value after applying the function to all elements in the collection.

    Examples:
        >>> reduce_([1, 2, 3, 4], lambda acc, x: acc + x, 0)
        10
    """

    acc = initial
    items = collection.values() if isinstance(collection, dict) else collection
    for v in items:
        acc = func(acc, v)
    return acc


def reduce_right(
    collection: Union[Dict[Any, Any], List[Any]], func: Callable, initial: Any
) -> Any:
    """
    Reduces a collection to a single accumulated value by applying a function from right to left.

    Args:
        collection: The collection to reduce, can be a dictionary or a list.
        func: A function that takes two arguments, the accumulator and the current value, and returns an updated accumulator.
        initial: The initial value for the accumulator.

    Returns:
        The final accumulated value after applying the function to all elements in the collection in reverse order.

    Examples:
        >>> reduce_right([1, 2, 3, 4], lambda acc, x: acc + x, 0)
        10
    """
    acc = initial
    items = (
        list(collection.values()) if isinstance(collection, dict) else list(collection)
    )
    for v in reversed(items):
        acc = func(acc, v)
    return acc


def reductions(
    collection: Union[Dict[Any, Any], List[Any]], func: Callable, initial: Any
) -> List[Any]:
    """
    Applies a rolling computation to sequential pairs of values in an iterable.

    Args:
        collection: An iterable to be reduced.
        func: A binary function to be applied to the items of the iterable.
        initializer: An initial value for the accumulator.

    Returns:
        A list of accumulated values.

    Examples:
        >>> reductions([1, 2, 3, 4], lambda x, y: x + y, 0)
        [1, 3, 6, 10]
    """
    acc = initial
    result: List[Any] = []
    items = collection.values() if isinstance(collection, dict) else collection
    for v in items:
        acc = func(acc, v)
        result.append(acc)
    return result


def reductions_right(
    collection: Union[Dict[Any, Any], List[Any]], func: Callable, initial: Any
) -> List[Any]:
    """
    Applies a rolling computation to sequential pairs of values in an iterable from right to left.

    Args:
        collection: An iterable to be reduced.
        func: A binary function to be applied to the items of the iterable.
        initializer: An initial value for the accumulator.

    Returns:
        A list of accumulated values.

    Examples:
        >>> reductions_right([1, 2, 3, 4], lambda x, y: x + y, 0)
        [10, 9, 7, 4]
    """
    acc = initial
    result: List[Any] = []
    items = (
        list(collection.values()) if isinstance(collection, dict) else list(collection)
    )
    for v in reversed(items):
        acc = func(acc, v)
        result.append(acc)
    return result


def sample_size(
    collection: Union[Dict[Any, Any], List[Any]], n: Optional[int] = None
) -> List[Any]:
    """
    Retrieves `n` random elements from a given `collection`.

    Args:
        collection: Collection to sample from.
        n: Number of items to sample.

    Returns:
        List of `n` sampled items.
    Note:
        The last element of the returned list would be the result of using
        :func:`sample`.

    Examples:
        >>> sample_size([1, 2, 3, 4], 2)
        [2, 4]
    """
    items = (
        list(collection.values()) if isinstance(collection, dict) else list(collection)
    )
    length = len(items)
    if n is None or n < 0:
        n = 1
    n = min(n, length)
    return random.sample(items, n)

def assign(target: Dict[Any, Any], *sources: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Assigns properties of source object(s) to the destination object.

    Args:
        target: Destination object whose properties will be modified.
        sources: Source objects to assign to `target`.

    Returns:
        Modified `target`.

    Warning:
        `target` is modified in place.

    Examples:
        >>> obj = {}
        >>> obj2 = assign(obj, {"a": 1}, {"b": 2}, {"c": 3})
        >>> obj == {"a": 1, "b": 2, "c": 3}
        True
        >>> obj is obj2
        True
    """
    for src in sources:
        for k, v in src.items():
            target[k] = v
    return target

def map_keys(
    obj: Dict[Any, Any], iteratee: Union[str, Callable[[Any], Any]]
) -> Dict[Any, Any]:
    """
    Creates an object with the same values but keys generated by running each key through iteratee.

    Args:
        obj: The dictionary to process.
        iteratee: A function or a string key used to generate the new keys. If a string is provided,
                  it is used to access the given key of each value in the dictionary.

    Returns:
        A new dictionary with values generated by iteratee as keys and original values as values.

    Examples:
        >>> map_keys({"a": {"b": 1}, "c": {"b": 2}}, "b")
        {1: {"b": 1}, 2: {"b": 2}}
    """
    if isinstance(iteratee, str):

        def fn(k, v):
            return (
                v.get(iteratee) if isinstance(v, dict) else getattr(v, iteratee, None)
            )
    else:
        fn = iteratee  # type: ignore
    out: Dict[Any, Any] = {}
    for k, v in obj.items():
        out[fn(k, v)] = v
    return out


def map_values(
    obj: Dict[Any, Any], iteratee: Union[str, Callable[[Any], Any]]
) -> Dict[Any, Any]:
    """
    Creates a new dictionary with the same keys but values generated by running each value
    of the input dictionary through the given iteratee.

    Args:
        obj: The dictionary to process.
        iteratee: A function or a string key used to generate the new values. If a string is provided,
                  it is used to access the given key of each value in the dictionary.

    Returns:
        A new dictionary with the original keys and values generated by the iteratee.

    Examples:
        >>> map_values({"a": {"b": 1}, "c": {"b": 2}}, "b")
        {'a': 1, 'c': 2}
    """

    if isinstance(iteratee, str):

        def fn(v):
            return (
                v.get(iteratee) if isinstance(v, dict) else getattr(v, iteratee, None)
            )
    else:
        fn = iteratee  # type: ignore
    return {k: fn(v) for k, v in obj.items()}


def rename_keys(obj: Dict[Any, Any], key_map: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Rename the keys of obj using key_map and return new object.

    Args:
        obj: Object to rename.
        key_map: Renaming map whose keys correspond to existing keys in obj and whose
            values are the new key name.

    Returns:
        Renamed obj.

    Examples:
        >>> obj = rename_keys({"a": 1, "b": 2, "c": 3}, {"a": "A", "b": "B"})
        >>> obj == {"A": 1, "B": 2, "c": 3}
        True
    """
    return {key_map.get(k, k): v for k, v in obj.items()}


def to_integer(value: Any) -> int:
    """
    Converts `value` to an integer. If conversion fails, returns 0.

    Args:
        value: The value to convert to an integer.

    Returns:
        Integer representation of the given value, or 0 if conversion fails.

    Examples:
        >>> to_integer(3.7)
        3
        >>> to_integer("42")
        42
        >>> to_integer("invalid")
        0
    """

    try:
        return int(float(value))
    except Exception:
        return 0

def to_string(value: Any) -> str:
    """
    Converts the given `value` to a string.

    Args:
        value: The value to convert to a string.

    Returns:
        String representation of the given `value`, or an empty string if `value` is None.

    Examples:
        >>> to_string(123)
        '123'
        >>> to_string(None)
        ''
    """

    return "" if value is None else str(value)


def to_list(value: Any) -> List[Any]:
    """
    Casts a value to a list: None -> [], tuples/sets -> list, others -> [value].

    Args:
        value: The value to convert to a list.

    Returns:
        List representation of the given `value`, or an empty list if `value` is None.

    Examples:
        >>> to_list(123)
        [123]
        >>> to_list(None)
        []
        >>> to_list([1, 2, 3])
        [1, 2, 3]
        >>> to_list((1, 2, 3))
        [1, 2, 3]
        >>> to_list({1, 2, 3})
        [1, 2, 3]
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]

            
def to_dict(value):
    """
    Convert a value to a dictionary.

    Args:
        value: The value to convert to a dictionary.

    Returns:
        A dictionary representation of the given value.

    Examples:

        >>> to_dict([1, 2, 3])
        {0: 1, 1: 2, 2: 3}
        >>> to_dict({"a": 1, "b": 2})
        {'a': 1, 'b': 2}
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, (list, tuple)):
        return {i: v for i, v in enumerate(value)}
    if hasattr(value, "items") and callable(getattr(value, "items")):
        return dict(value.items())
    try:
        return dict(value)  # best-effort
    except Exception:
        return {}


def keys(obj):
    """
    Return the keys of a dictionary, or a range of indices if the object is a list/tuple,
    or the keys of a __dict__ if the object has one. Otherwise, return an empty list.

    Args:
        obj: The object to get keys from.

    Returns:
        A list of keys.

    Examples:
        >>> keys({"a": 1, "b": 2})
        ["a", "b"]
        >>> keys([1, 2, 3])
        [0, 1, 2]
        >>> keys({"a": 1, "b": 2}.__dict__)
        ["a", "b"]
    """
    if isinstance(obj, dict):
        return list(obj.keys())
    if isinstance(obj, (list, tuple)):
        return list(range(len(obj)))
    if hasattr(obj, "keys") and callable(getattr(obj, "keys")):
        return list(obj.keys())
    if hasattr(obj, "__dict__"):
        return list(obj.__dict__.keys())
    return []


def values(obj):
    """
    Return the values of a dictionary, or the elements of a list/tuple, or the values of a __dict__ if the object has one. Otherwise, return an empty list.

    Args:
        obj: The object to get values from.

    Returns:
        A list of values.

    Examples:
        >>> values({"a": 1, "b": 2})
        [1, 2]
        >>> values([1, 2, 3])
        [1, 2, 3]
        >>> values({"a": 1, "b": 2}.__dict__)
        [1, 2]
    """
    if isinstance(obj, dict):
        return list(obj.values())
    if isinstance(obj, (list, tuple)):
        return list(obj)
    if hasattr(obj, "values") and callable(getattr(obj, "values")):
        return list(obj.values())
    if hasattr(obj, "__dict__"):
        return list(obj.__dict__.values())
    return []


def to_pairs(obj) -> list:
    """
    Convert obj into an array of [key, value] pairs.

    Args:
        obj: The dictionary, list, tuple, or other object to convert

    Returns:
        A list of key-value tuples

    Examples:
        >>> to_pairs({"a": 1, "b": 2})
        [("a", 1), ("b", 2)]
        >>> to_pairs([1, 2, 3])
        [(0, 1), (1, 2), (2, 3)]
    """
    return list(_iter_items_like(obj))


def callables(obj) -> list:
    """
    Return a list of the keys of all callable values in obj.

    Args:
        obj: The object to search

    Returns:
        A list of keys of callable values

    Examples:
        >>> callables({"a": 1, "b": lambda x: x})
        ["b"]
    """
    return [k for k, v in _iter_items_like(obj) if callable(v)]


def invert(obj):

    """
    Invert a dictionary or list/tuple, or make a best effort at doing so
    on any items-like object.
    Dict: {k:v} -> {v:k}; List/Tuple: [v0,v1,...] -> {v0:0, v1:1, ...}
    
    Args:
        obj: The dictionary, list, tuple, or other object to invert

    Returns:
        A dictionary with the values of the input as keys and the keys as
        values (or indices for lists/tuples)

    Examples:
        >>> invert({"a": 1, "b": 2})
        {1: "a", 2: "b"}
        >>> invert([1, 2, 3])
        {1: 0, 2: 1, 3: 2}
    """
    if isinstance(obj, dict):
        return {v: k for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return {v: i for i, v in enumerate(obj)}
    # best-effort on items-like
    return {v: k for k, v in _iter_items_like(obj)}


def invert_by(obj, iteratee=None):
    """
    Invert a dictionary or list/tuple, or make a best effort at doing so
    on any items-like object, with an optional iteratee to transform the
    values to be used as keys in the inverted object.

    Args:
        obj: The dictionary, list, tuple, or other object to invert
        iteratee: An optional callable that takes a value and returns a key
            value to use in the inverted object. If not provided, the values
            will be used as-is.

    Returns:
        A dictionary with the transformed values as keys, and lists of the
        original keys as values.

    Examples:
        >>> invert_by({"a": 1, "b": 2}, lambda x: x * 2)
        {2: ["a"], 4: ["b"]}
        >>> invert_by([1, 2, 3], lambda x: "x{}".format(x))
        {"x1": [0], "x2": [1], "x3": [2]}
    """
    fn = iteratee or (lambda x: x)
    out: Dict[Any, List[Any]] = {}
    for k, v in _iter_items_like(obj):
        key_val = fn(v)
        out.setdefault(key_val, []).append(k)
    return out

def unset(obj, path) -> bool:
    """
    Removes the property at `path` of `obj`.

    Args:
        obj: The object to modify.
        path: The path of the property to unset.

    Returns:
        Whether the property was deleted.

    Warning:
        `obj` is modified in place.

    Examples:
        >>> obj = {"a": [{"b": {"c": 7}}]}
        >>> unset(obj, "a[0].b.c")
        True
        >>> obj
        {'a': [{'b': {}}]}
        >>> unset(obj, "a[0].b.c")
        False
    """
    parts = _as_parts_any(path)
    if not parts:
        return False

    cur = obj
    for part in parts[:-1]:
        if isinstance(cur, dict):
            if part not in cur:
                return False
            cur = cur[part]
        elif isinstance(cur, list) and isinstance(part, int):
            if part < 0 or part >= len(cur):
                return False
            cur = cur[part]
        else:
            if not hasattr(cur, str(part)):
                return False
            cur = getattr(cur, str(part))

    last = parts[-1]

    if isinstance(cur, dict):
        val = cur.pop(last, _MISSING)
        return val is not _MISSING

    if isinstance(cur, list) and isinstance(last, int):
        if 0 <= last < len(cur):
            # list.pop accepts only the index (no default)
            cur.pop(last)
            return True
        return False

    if hasattr(cur, str(last)):
        try:
            delattr(cur, str(last))
            return True
        except Exception:
            return False

    return False


def update(obj, path, updater):
    """
    Update value at `path` by applying `updater` (or using it as a constant).

    Args:
        obj: The object to modify.
        path: The path of the property to update.
        updater: Function that returns updated value.

    Returns:
        Updated `obj`.

    Warning:
        `obj` is modified in place.

    Examples:
        >>> obj = {"a": [{"b": {"c": 7}}]}
        >>> update(obj, "a[0].b.c", lambda x: x**2)
        {'a': [{'b': {'c': 49}}]}
    """
    current = get(obj, path, None)
    newval = updater(current)
    set_(obj, path, newval)
    return obj

def find_last_key(obj, predicate=None):
    """
    Finds the last key of a dictionary or list that satisfies the predicate.

    Args:
        obj: The dictionary or list to search.
        predicate: An optional function that returns True for elements to include.
                   If not provided, the truthiness of the element itself is used.

    Returns:
        The last key that satisfies the predicate, or None if not found.

    Examples:
        >>> find_last_key({'a': 1, 'b': 2, 'c': 3}, lambda x: x > 1)
        'c'
    """
    pairs = list(_iter_items_like(obj))
    pred = predicate or (lambda _: True)
    for k, v in reversed(pairs):
        if pred(v):
            return k
    return None


def for_in(obj, iteratee):
    """
    Iterate over an object (dict or sequence), calling `iteratee` for each element.

    Args:
        obj: The object to iterate over.
        iteratee: A function of three arguments: `(value, key, obj)`.
                  Return `False` to break the loop.

    Returns:
        The original `obj`.

    Examples:

        >>> obj = {"a": 1, "b": 2}
        >>> for_in(obj, lambda v, k, o: print(f"{k}: {v}"))
        a: 1
        b: 2
        >>> obj
        {'a': 1, 'b': 2}
    """
    for k, v in _iter_items_like(obj):
        res = iteratee(v, k, obj)
        if res is False:
            break
    return obj


def for_in_right(obj, iteratee):
    """
    Iterate over an object (dict or sequence) in reverse order, calling `iteratee` for each element.

    Args:
        obj: The object to iterate over.
        iteratee: A function of three arguments: `(value, key, obj)`.
                  Return `False` to break the loop.

    Returns:
        The original `obj`.

    Examples:

        >>> obj = {"a": 1, "b": 2}
        >>> for_in_right(obj, lambda v, k, o: print(f"{k}: {v}"))
        b: 2
        a: 1
        >>> obj
        {'a': 1, 'b': 2}
    """
    pairs = list(_iter_items_like(obj))
    for k, v in reversed(pairs):
        res = iteratee(v, k, obj)
        if res is False:
            break
    return obj


def clone(obj: Union[Dict, List]) -> Union[Dict, List]:
    """
    Creates a shallow copy of an object (dictionary or list).

    Args:
        obj: The object to clone.

    Returns:
        A new object that is a shallow copy of `obj`.

    Examples:

        >>> obj = {"a": 1, "b": 2}
        >>> cloned = _.clone(obj)
        >>> cloned
        {'a': 1, 'b': 2}
    """
    if isinstance(obj, dict):
        return obj.copy()
    if isinstance(obj, list):
        return list(obj)
    return obj


def clone_deep(obj: Any) -> Any:
    """
    Creates a deep copy of an object.

    Args:
        obj: The object to clone.

    Returns:
        A new object that is a deep copy of `obj`.

    Note:
        This function will not clone functions, methods, or modules.

    Examples:
        >>> obj = {"a": 1, "b": 2}
        >>> cloned = _.clone_deep(obj)
        >>> cloned
        {'a': 1, 'b': 2}
    """
    memo: Dict[int, Any] = {}
    stack: list[tuple[Any, Any | None, Any | None]] = [(obj, None, None)]
    root: Any = None

    while stack:
        src, parent, key = stack.pop()
        sid = id(src)
        if sid in memo:
            val = memo[sid]
        elif isinstance(src, dict):
            val = {}
            memo[sid] = val
            # push children
            for k, v in src.items():
                stack.append((v, val, k))
        elif isinstance(src, list):
            val = []
            memo[sid] = val
            for i, v in enumerate(src):
                stack.append((v, val, i))
        else:
            # immutable or custom object
            try:
                val = src.__class__(src) if hasattr(src, "__iter__") and not isinstance(src, (str, bytes, bytearray)) else src
            except Exception:
                val = src
            memo[sid] = val

        if parent is None:
            root = val
        else:
            if isinstance(parent, list) and isinstance(key, int):
                _ensure_len(parent, key + 1)
                parent[key] = val
            else:
                parent[key] = val # type: ignore

    return root


def clone_deep_with(obj: Any, customizer: Callable) -> Any:
    """
    Creates a deep clone of `obj` with a customizer. The customizer may take:
      (value, key, parent)  or (value, key)  or (value)

    Args:
        obj: Object to clone.
        customizer: Customizer function.

    Returns:
        Cloned object.

    Examples:
        >>> obj = {"a": 1, "b": 2}
        >>> cloned = _.clone_deep_with(obj, lambda x: x + 1)
        >>> cloned
        {'a': 2, 'b': 3}
    """
    def _clone(x, key=None, parent=None):
        customized = _call_customizer(customizer, x, key, parent)
        if customized is not None:
            return customized
        if isinstance(x, dict):
            return {k: _clone(v, k, x) for k, v in x.items()}
        if isinstance(x, list):
            return [_clone(v, i, x) for i, v in enumerate(x)]
        return x

    return _clone(obj)


def defaults_deep(target: Dict[Any, Any], *sources: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Assigns properties of source object(s) to the destination object for all destination properties
    that resolve to undefined. This method is like :func:`defaults` except that it recursively assigns
    default properties.

    Args:
        target: Destination object whose properties will be modified.
        sources: Source objects to assign to `target`.

    Returns:
        Modified `target`.

    Warning:
        `target` is modified in place.

    Examples:
        >>> obj = {"a": 1}
        >>> obj2 = defaults_deep(obj, {"b": 2}, {"c": 3}, {"a": 4})
        >>> obj is obj2
        True
        >>> obj == {"a": 1, "b": 2, "c": 3}
        True
    """
    def _dd(a, b):
        # both dicts
        if isinstance(a, dict) and isinstance(b, dict):
            for k, v in b.items():
                if k in a:
                    a[k] = _dd(a[k], v)
                else:
                    a[k] = clone_deep(v) if isinstance(v, (dict, list)) else v
            return a
        # element-wise lists-of-dicts merge (no append)
        if isinstance(a, list) and isinstance(b, list):
            m = min(len(a), len(b))
            for i in range(m):
                if isinstance(a[i], dict) and isinstance(b[i], dict):
                    a[i] = _dd(a[i], b[i])
            return a
        # if a already set, keep it
        return (
            a if a is not None else clone_deep(b) if isinstance(b, (dict, list)) else b
        )

    for src in sources:
        if isinstance(src, dict):
            target = _dd(target, src) # type: ignore
    return target


def merge(*objects: Any) -> Any:
    """
    Deep merge dictionaries. Special cases:
      - If called with a single list, returns a deep clone of the list.
      - If called with a single None, returns None.
      - Lists under the same key are merged element-wise (no appending new items
        unless one side is longer); dict elements at the same index are merged
        recursively; non-dict/list elements prefer the right side.
    Args:
        objects: Objects to merge.

    Returns:
        Merged object.

    Warning:
        Objects are modified in place.  If you need a copy, use :func:`clone_deep`.
        
    Examples:

        >>> obj = {"a": 1}
        >>> obj2 = merge(obj, {"b": 2}, {"c": 3}, {"a": 4})
        >>> obj is obj2
        True
        >>> obj == {"a": 4, "b": 2, "c": 3}
        True
    """
    if not objects:
        return {}

    head = objects[0]

    # Pass-through semantics for single arg cases
    if len(objects) == 1 and (head is None or isinstance(head, list)):
        return clone_deep(head) if isinstance(head, list) else head
    if head is None:
        return None

    def _merge_two(a: Any, b: Any) -> Any:
        # If either isn’t a dict, prefer b unless b is None
        if not isinstance(a, dict) or not isinstance(b, dict):
            if isinstance(a, (dict, list)) and b is None:
                return clone_deep(a)
            if isinstance(b, (dict, list)):
                return clone_deep(b)
            return b if b is not None else a

        # Both dicts: start with a (cloned where needed), then fold in b
        res: Dict[Any, Any] = {
            k: clone_deep(v) if isinstance(v, (dict, list)) else v
            for k, v in a.items()
        }

        for k, v in b.items():
            if k in res:
                av = res[k]
                if isinstance(av, dict) and isinstance(v, dict):
                    res[k] = _merge_two(av, v)
                elif isinstance(av, list) and isinstance(v, list):
                    # Element-wise merge for lists (no blind append)
                    m = max(len(av), len(v))
                    out: List[Any] = []
                    for i in range(m):
                        if i < len(av) and i < len(v) and isinstance(av[i], dict) and isinstance(v[i], dict):
                            out.append(_merge_two(av[i], v[i]))
                        elif i < len(av) and i < len(v):
                            out.append(clone_deep(v[i]))
                        elif i < len(av):
                            out.append(clone_deep(av[i]))
                        else:
                            out.append(clone_deep(v[i]))
                    res[k] = out
                else:
                    res[k] = clone_deep(v) if isinstance(v, (dict, list)) else v
            else:
                res[k] = clone_deep(v) if isinstance(v, (dict, list)) else v

        return res

    result: Any = head if isinstance(head, dict) else {}
    # If head is a dict, fold remaining dicts into it; otherwise just fold all dicts
    for o in (objects[1:] if isinstance(head, dict) else objects):
        if isinstance(o, dict):
            result = _merge_two(result, o) if result else clone_deep(o)
        elif result == {} and o in (None, [], {}):
            # ignore empty-ish inputs
            continue

    return result

def omit(obj, *keys_to_omit):
    """
    Omit properties from an object.

    Args:
        obj: The object to omit properties from.
        *keys_to_omit: Property names to omit.

    Returns:
        A new object with omitted properties.

    Examples:

        >>> omit({"a": 1, "b": 2, "c": 3}, "b", "c") == {"a": 1}
        True
        >>> omit({"a": 1, "b": 2, "c": 3}, ["a", "c"]) == {"b": 2}
        True
    """
    keys_flat = _flatten_keys(keys_to_omit)
    if isinstance(obj, (list, tuple)):
        base = to_dict(obj)
        return {k: v for k, v in base.items() if k not in keys_flat}
    base = dict(_iter_items_like(obj)) if not isinstance(obj, dict) else obj
    # deep path omit (e.g., "a.b[0].c")
    simple_keys = [
        k
        for k in keys_flat
        if not isinstance(k, str) or ("." not in k and "[" not in k)
    ]
    out = {k: v for k, v in base.items() if k not in simple_keys}
    # handle deep string paths
    for p in keys_flat:
        if isinstance(p, str) and (("." in p) or ("[" in p)):
            unset(out, p)
    return out


def omit_by(obj, predicate=None):
    """
    Omit properties from an object using a predicate.

    Args:
        obj: The object to omit properties from.
        predicate: A predicate function that takes two arguments (value, key) and
            returns True if the property should be omitted or False if it should
            be kept.

    Returns:
        A new object with omitted properties.

    Examples:
        >>> omit_by({"a": 1, "b": 2, "c": 3}, lambda v, k: k.startswith("b")) == {"a": 1, "c": 3}
        True
    """
    if predicate is None:
        return to_dict(obj)
    if isinstance(predicate, (list, tuple, set)):
        return {k: v for k, v in to_dict(obj).items() if k not in predicate}
    return {k: v for k, v in _iter_items_like(obj) if not predicate(v, k)}


def assign_with(target: dict, *sources, customizer=None) -> dict:
    """
    Assigns properties of source object(s) to the destination object.

    Args:
        target: Destination object whose properties will be modified.
        sources: Source objects to assign to `target`.
        customizer: Customizer applied per iteration.

    Returns:
        Modified `target`.

    Warning:
        `target` is modified in place.

    Examples:

        >>> target = {"a": 1}
        >>> assign_with(target, {"b": 2}, lambda o, s, k, t: s if o is None else o)
        {'a': 1, 'b': 2}
    """
    if customizer is None and sources and callable(sources[-1]):
        *sources, customizer = sources
    if customizer is None or not callable(customizer):
        raise TypeError("assign_with() missing 1 required argument: 'customizer'")

    for src in sources:
        if not isinstance(src, dict):
            try:
                src = dict(src)
            except Exception:
                continue
        for k, v in src.items():
            obj_val = target.get(k, None)
            # flexible-arity customizer: (obj_val, src_val, key, target) → fewer args if needed
            try:
                newv = customizer(obj_val, v, k, target)
            except TypeError:
                try:
                    newv = customizer(obj_val, v, k)
                except TypeError:
                    try:
                        newv = customizer(obj_val, v)
                    except TypeError:
                        newv = customizer(v)
            target[k] = v if newv is None else newv
    return target

def find_key(obj, predicate=None):
    """
    Finds the first key of a dictionary or list that satisfies the predicate.

    Args:
        obj: The dictionary or list to search.
        predicate: An optional function that returns True for elements to include.
                   If not provided, the truthiness of the element itself is used.

    Returns:
        The first key that satisfies the predicate, or None if not found.

    Examples:

        >>> find_key({"a": 1, "b": 2, "c": 3}, lambda x: x > 1)
        'b'
    """
    pred = predicate or (lambda v: bool(v))
    for k, v in _iter_items_like(obj):
        if pred(v):
            return k
    return None

def map_values_deep(obj: Any, fn: Callable[..., Any]) -> Any:
    """
    Map all non-object values in `obj` with return values from `fn`. The iteratee is invoked
    with two arguments: ``(obj_value, property_path)`` where ``property_path`` contains the list of
    path keys corresponding to the path of ``obj_value``.

    Args:
        obj: Object to map.
        fn: Iteratee applied to each value.

    Returns:
        The modified object.

    Warning:
        `obj` is modified in place.

    Examples:
        >>> x = {"a": 1, "b": {"c": 2}}
        >>> y = map_values_deep(x, lambda val: val * 2)
        >>> y == {"a": 2, "b": {"c": 4}}
        True
        >>> z = map_values_deep(x, lambda val, props: props)
        >>> z == {"a": ["a"], "b": {"c": ["b", "c"]}}
        True
    """
    def _walk(x: Any, path: List[Union[str, int]]) -> Any:
        if isinstance(x, dict):
            return {k: _walk(v, path + [k]) for k, v in x.items()}
        if isinstance(x, list):
            return [_walk(v, path + [i]) for i, v in enumerate(x)]
        try:
            return fn(x, path)          # (value, property_path)
        except TypeError:
            return fn(x)                # (value) fallback
    return _walk(obj, [])


def apply(fn: Callable[..., U], *args: Any, **kwargs: Any) -> U:
    """
    Applies a function to some arguments. Supports functions with variable arity, functions with keyword arguments, and functions with default arguments.

    Args:
        fn: The function to apply.
        *args: The positional arguments to apply the function to.
        **kwargs: The keyword arguments to apply the function with.

    Returns:
        The result of applying the function to the arguments.

    Examples:

        >>> apply(lambda x, y: x + y, 1, 2)
        3
    """
    real_fn, a, kw = _split_apply_args(fn, *args, **kwargs)
    return real_fn(*a, **kw)


def apply_if_not_none(fn: Callable[..., U], *args: Any, **kwargs: Any) -> Optional[U]:
    """
    Applies a function to some arguments if none of the arguments are None. Otherwise, return None.

    Args:
        fn: The function to apply.
        *args: The positional arguments to apply the function to.
        **kwargs: The keyword arguments to apply the function with.

    Returns:
        The result of applying the function to the arguments, or None if any of the arguments are None.

    Examples:

        >>> apply_if_not_none(lambda x, y: x + y, 1, 2)
        3
        >>> apply_if_not_none(lambda x, y: x + y, 1, None)
        None
    """
    real_fn, a, kw = _split_apply_args(fn, *args, **kwargs)
    if all(arg is not None for arg in a):
        return real_fn(*a, **kw)
    return None


# SHALLOW clone_with: apply customizer at the first level only.
def clone_with(obj: Any, customizer: Callable[..., Any]) -> Any:
    """
    Creates a shallow clone of `obj` with a customizer. The customizer may take:
      (value, key, parent)  or (value, key)  or (value)

    Args:
        obj: Object to clone.
        customizer: Customizer function.

    Returns:
        Cloned object.

    Examples:
        >>> obj = {"a": 1, "b": 2}
        >>> cloned = _.clone_with(obj, lambda x: x + 1)
        >>> cloned
        {'a': 2, 'b': 3}
    """
    def _call(v, k=None, p=None):
        try:
            return customizer(v, k, p)
        except TypeError:
            try:
                return customizer(v, k)
            except TypeError:
                return customizer(v)

    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            nv = _call(v, k, obj)
            out[k] = v if nv is None else nv
        return out
    if isinstance(obj, list):
        out = []
        for i, v in enumerate(obj):
            nv = _call(v, i, obj)
            out.append(v if nv is None else nv)
        return out
    # non-container: customizer can override value, else return as-is
    nv = _call(obj)
    return obj if nv is None else nv

def get(obj: Any, path: Union[str, Iterable[Any], Any], default: Any = None) -> Any:
    """
    Return the value at `path` from `obj`. If not set, returns `default`.

    Args:
        obj: Object to resolve the path on.
        path: The path to resolve.
        default: The value to return if `path` is not set.

    Returns:
        The value at `path`, or `default`.

    Examples:
        >>> get({"a": {"b": 1}}, "a.b")
        1
        >>> get({"a": {"b": 1}}, "a.c", 42)
        42
    """
    parts = _as_parts_any(path)
    for p in parts:
        if isinstance(p, str) and p in _RESTRICTED:
            if isinstance(obj, (dict, list)):
                return default
            raise KeyError("access to restricted key")

    cur = obj
    for seg in parts:
        if cur is None:
            return default

        # dict
        if isinstance(cur, dict):
            if seg in cur:
                cur = cur[seg]
                continue
            # int<->str coercion
            if isinstance(seg, str) and _is_int_str(seg):
                i = int(seg)
                if i in cur:
                    cur = cur[i]
                    continue
            if isinstance(seg, int):
                s = str(seg)
                if s in cur:
                    cur = cur[s]
                    continue
            return default

        # list (strict index)
        if isinstance(cur, list):
            if isinstance(seg, int) or (isinstance(seg, str) and _is_int_str(seg)):
                idx = seg if isinstance(seg, int) else int(seg)
                if -len(cur) <= idx < len(cur):
                    cur = cur[idx]
                    continue
            return default

        # namedtuple (field or index)
        if isinstance(cur, tuple) and hasattr(cur, "_fields"):
            if isinstance(seg, str) and seg in getattr(cur, "_fields", ()):
                cur = getattr(cur, seg)
                continue
            if isinstance(seg, int) or (isinstance(seg, str) and _is_int_str(seg)):
                idx = seg if isinstance(seg, int) else int(seg)
                if -len(cur) <= idx < len(cur):
                    cur = cur[idx]
                    continue
            return default

        # generic non-string sequence (e.g., range)
        if isinstance(cur, AbcSequence) and not isinstance(cur, (str, bytes, bytearray)):
            if isinstance(seg, int) or (isinstance(seg, str) and _is_int_str(seg)):
                idx = seg if isinstance(seg, int) else int(seg)
                L = len(cur)
                if -L <= idx < L:
                    cur = cur[idx]
                    continue
            return default

        # object attribute (never return callables)
        attr = getattr(cur, str(seg), _MISSING)
        if attr is _MISSING or callable(attr):
            return default
        cur = attr

    return cur


def merge_with(*objects, customizer=None):
    """
    Merges objects using a customizer.

    Args:
        *objects: Objects to merge.
        customizer: Customizer function. If `None`, falls back to `merge`.

    Returns:
        Merged object.

    Warning:
        Modified in place.

    Examples:
        >>> merge_with({"a": 1}, {"b": 2}, lambda x, y, key, parent: x + y if key == "a" else y)
        {"a": 3, "b": 2}
    """
    if customizer is None and objects and callable(objects[-1]):
        *objects, customizer = objects
    if not objects:
        return {}
    if customizer is None:
        return merge(*objects)

    def _call_c(obj_val, src_val, key=None, parent=None):
        try:
            return customizer(obj_val, src_val, key, parent)
        except TypeError:
            try:
                return customizer(obj_val, src_val, key)
            except TypeError:
                try:
                    return customizer(obj_val, src_val)
                except TypeError:
                    return customizer(src_val)

    def _merge(a, b, parent=None, key=None):
        # Give customizer first shot
        cv = _call_c(a, b, key, parent)
        if cv is not None:
            return cv

        # default deep behavior
        if isinstance(a, dict) and isinstance(b, dict):
            out = {k: clone_deep(v) if isinstance(v, (dict, list)) else v for k, v in a.items()} # type: ignore
            for k2, v2 in b.items():
                if k2 in out:
                    out[k2] = _merge(out[k2], v2, out, k2)
                else:
                    out[k2] = clone_deep(v2) if isinstance(v2, (dict, list)) else v2
            return out

        if isinstance(a, list) and isinstance(b, list):
            # default: element-wise (your merge semantics)
            m = max(len(a), len(b))
            out: List[Any] = []
            for i in range(m):
                if i < len(a) and i < len(b) and isinstance(a[i], dict) and isinstance(b[i], dict):
                    out.append(_merge(a[i], b[i], a, i))
                elif i < len(a) and i < len(b):
                    out.append(clone_deep(b[i]))
                elif i < len(a):
                    out.append(clone_deep(a[i]))
                else:
                    out.append(clone_deep(b[i]))
            return out

        # scalar or mismatched types: prefer b unless b is None
        if isinstance(b, (dict, list)):
            return clone_deep(b)
        return b if b is not None else a

    head, *rest = objects
    result = clone_deep(head) if isinstance(head, (dict, list)) else head
    for idx, nxt in enumerate(rest):
        result = _merge(result, nxt, None, None)
    return result

def parse_int(value: Any, radix: Optional[int] = None) -> Optional[int]:
    """
    Converts the given `value` into an integer of the specified `radix`. If `radix` is falsey, a
    radix of ``10`` is used unless the `value` is a hexadecimal, in which case a radix of 16 is
    used.

    Args:
        value: Value to parse.
        radix: Base to convert to.

    Returns:
        Integer if parsable else ``None``.

    Examples:
        >>> parse_int("5")
        5
        >>> parse_int("12", 8)
        10
        >>> parse_int("x") is None
        True
    """
    if isinstance(value, bool):
        return int(value)

    # If no radix is specified, numbers parse naturally
    if radix is None and isinstance(value, (int, float)):
        try:
            return int(value)
        except Exception:
            return None

    # Otherwise parse the *string* with the requested base
    s = str(value).strip()
    try:
        base = 16 if radix is None else (0 if radix == 0 else radix)
        return int(s, base)
    except Exception:
        return None
    

def pick(obj, *keys_to_pick):
    """
    Creates an object composed of the picked `keys_to_pick` from `obj`.

    Args:
        obj: Object to pick from.
        *keys_to_pick: Keys to pick.

    Returns:
        Object composed of picked keys.

    Examples:

        >>> pick({"a": 1, "b": 2, "c": 3, "d": 4}, "a", "d")
        {"a": 1, "d": 4}
    """
    if not keys_to_pick:
        return {}
    out: Dict[Any, Any] = {}
    deep_paths, flat_keys = [], set()

    for p in _flatten_keys(keys_to_pick):
        if isinstance(p, list) or (isinstance(p, str) and ('.' in p or '[' in p)):
            deep_paths.append(p)
        else:
            flat_keys.add(p)

    # single pass for top-level keys
    if flat_keys:
        for k, v in _iter_items_like(obj):
            if k in flat_keys:
                out[k] = v

    # deep paths
    for p in deep_paths:
        parts = p if isinstance(p, list) else _as_parts_any(p)
        val = get(obj, parts, _MISSING)
        if val is not _MISSING:
            _set_by_path(out, parts, val, obj)

    return out

def pick_by(obj, predicate=None):
    """
    Creates an object composed of the picked object properties.

    Args:
        obj: Object to pick from.
        predicate: Predicate used to determine which properties to pick.

    Returns:
        Object composed of picked properties.

    Examples:
        >>> pick_by({"a": 1, "b": 2, "c": 3}, lambda v, k: k in ("a", "c"))
        {"a": 1, "c": 3}
    """
    if predicate is None:
        return to_dict(obj)
    if isinstance(predicate, (list, tuple, set)):
        keys = set(predicate)
        return {k: v for k, v in _iter_items_like(obj) if k in keys}
    if isinstance(predicate, str):
        key = predicate
        return {k: v for k, v in _iter_items_like(obj) if k == key}
    # callable(value, key)
    return {k: v for k, v in _iter_items_like(obj) if predicate(v, k)}
def to_boolean(
    value: Any,
    true_patterns: Optional[Iterable[str]] = None,
    false_patterns: Optional[Iterable[str]] = None,
) -> Optional[bool]:
    if isinstance(value, str):
        s = value.strip()
        if true_patterns:
            for p in true_patterns:
                if re.search(p, s, flags=re.IGNORECASE):
                    return True
        if false_patterns:
            for p in false_patterns:
                if re.search(p, s, flags=re.IGNORECASE):
                    return False
        if s == "":
            return None
        lower = s.lower()
        if lower in {"true", "1", "yes", "on"}:
            return True
        if lower in {"false", "0", "no", "off"}:
            return False
        return None
    return bool(value)

def transform(
    obj: Union[Dict[Any, Any], List[Any]],
    func: Optional[Callable[..., Any]] = None,
    accumulator: Optional[Any] = None,
) -> Any:
    """
    Transforms an object by applying a function to each item in the object.

    Args:
        obj: The object to transform
        func: A function to apply to each item in the object. It takes either 2 or 3 arguments
            depending on the type of the object.
            If obj is a dict, the arguments are (accumulator, value, key).
            If obj is a list, the arguments are (accumulator, value, index).
            If func returns False, the iteration will be stopped.
        accumulator: The initial accumulator value. If not provided, it will be set to an empty
            dict if obj is a dict, or an empty list if obj is a list

    Returns:
        The accumulator after applying the function to all items in the object.

    Examples:

        >>> transform({"a": 1, "b": 2}, lambda acc, v, k: acc.update({k: v + 1}))
        {"a": 2, "b": 3}
    """
    if accumulator is None:
        accumulator = {} if isinstance(obj, dict) else []
    if func is None:
        # No iteratee => leave accumulator unchanged
        return accumulator

    sig = inspect.signature(func)
    arity = sum(1 for p in sig.parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD))

    items = obj.items() if isinstance(obj, dict) else enumerate(obj)
    for k, v in items:
        res = func(accumulator, v, k) if arity >= 3 else func(accumulator, v)
        if res is False:
            break
    return accumulator

def to_number(value: Any, precision: Optional[int] = 0) -> Optional[float]:
    """
    Convert `value` to a number. All numbers are retuned as ``float``. If precision is negative, round
    `value` to the nearest positive integer place. If `value` can't be converted to a number, ``None``
    is returned.

    Args:
        value: Object to convert.
        precision: Precision to round number to. Defaults to ``0``.

    Returns:
        Converted number or ``None`` if it can't be converted.

    Examples:
        >>> to_number("1234.5678")
        1235.0
        >>> to_number("1234.5678", 4)
        1234.5678
        >>> to_number(1, 2)
        1.0
    """
    try:
        num = float(value)
    except Exception:
        return None
    if precision is None:
        return num
    if precision >= 0:
        return round(num, precision)
    factor = 10 ** (-precision)
    return math.floor(num / factor) * factor

def set_(obj, path, value):
    """
    Set `value` at `path`, creating intermediate containers.
    Supports escaped dots and bracket literals via _as_parts_any().

    Args:
        obj: The object to modify.
        path: The path of the property to set.
        value: The value to set.

    Returns:
        Updated `obj`.

    Examples:
        >>> obj = {"a": [{"b": {"c": 7}}]}
        >>> set_(obj, "a[0].b.c", 8)
        {'a': [{'b': {'c': 8}}]}
    """
    parts = _as_parts_any(path)
    if not parts:
        return obj

    cur = obj
    for i, seg in enumerate(parts[:-1]):
        prefer_list = isinstance(parts[i + 1], int)
        if isinstance(cur, dict):
            cur, _ = _ensure_container(cur, seg, None, prefer_list_index=prefer_list)
        elif isinstance(cur, list) and isinstance(seg, int):
            cur, _ = _ensure_container(cur, seg, None, prefer_list_index=prefer_list)
        else:
            cur, _ = _ensure_container(cur, str(seg), None, prefer_list_index=prefer_list)

    last = parts[-1]
    if isinstance(cur, dict):
        cur[last] = value
    elif isinstance(cur, list) and isinstance(last, int):
        while len(cur) <= last:
            cur.append(None)
        cur[last] = value
    else:
        setattr(cur, str(last), value)
    return obj

def set_with(obj, path, value, customizer):
    """
    Set `value` at `path`, creating intermediate containers.
    Supports escaped dots and bracket literals via _as_parts_any().
    If `customizer` is callable, it's invoked to produce the objects of path.
    If `customizer` returns undefined path creation is handled by the method
    instead. The customizer is invoked with three arguments: ``(nested_value, key, nested_object)``.

    Args:
        obj: Object to modify.
        path: The path to set value to.
        value: The value to set.
        customizer: The function to customize assigned values.

    Returns:
        Modified `obj`.

    Warning:
        `obj` is modified in place.

    Examples:
        >>> set_with({}, "[0][1]", "a", lambda: {})
        {0: {1: 'a'}}
    """
    def make():
        if callable(customizer):
            return customizer()
        if isinstance(customizer, list):
            return []
        return {}

    parts = _parse_path(path) if isinstance(path, str) else ([path] if isinstance(path, int) else list(path))
    cur = obj
    for i, seg in enumerate(parts):
        last = (i == len(parts) - 1)
        if last:
            if isinstance(cur, list) and isinstance(seg, int):
                while len(cur) <= seg:
                    cur.append(None)
                cur[seg] = value
            elif isinstance(cur, dict):
                cur[seg] = value
            else:
                setattr(cur, str(seg), value)
            return obj

        # Not last: descend, creating with customizer only when needed
        if isinstance(cur, list) and isinstance(seg, int):
            while len(cur) <= seg:
                cur.append(None)
            child = cur[seg]
            if not _is_containerish(child):
                child = make()
                cur[seg] = child
            cur = child
        elif isinstance(cur, dict):
            child = cur.get(seg, None)
            if not _is_containerish(child):
                child = make()
                cur[seg] = child
            cur = child
        else:
            sentinel = _MISSING
            child = getattr(cur, str(seg), sentinel)
            if child is sentinel or not _is_containerish(child):
                child = make()
                setattr(cur, str(seg), child)
            cur = child

    return obj

def update_with(obj, path, func, customizer):
    """
    Update value at `path` by applying `func` (or using it as a constant).

    Args:
        obj: The object to modify.
        path: The path of the property to update.
        func: Function that returns updated value.
        customizer: The function to customize assigned values.

    Returns:
        Modified `obj`.

    Warning:
        `obj` is modified in place.

    Examples:

        >>> obj = {"a": [{"b": {"c": 7}}]}
        >>> update_with(obj, "a[0].b.c", lambda x: x**2, dict)
        {'a': [{'b': {'c': 49}}]}
    """
    current = get(obj, path)
    if callable(func):
        try:
            new_val = func(current)
        except TypeError:
            new_val = func()
    else:
        new_val = func
    return set_with(obj, path, new_val, customizer)

def apply_if(*args, **kwargs):
    """Apply a function to a *value* only if `predicate(value)` is True.

    Accepted forms:
      - value-first (preferred): apply_if(value, fn, predicate)
      - legacy: apply_if(fn, predicate, *args, **kwargs)

    Args:
        *args: The arguments to apply the function to.
        **kwargs: The keyword arguments to apply the function with.

    Returns:
        The result of the function, or None if the predicate is false.
    
    Examples:
        >>> apply_if(1, lambda x: x + 1, lambda x: x > 0)
        2
    """
    if args and not callable(args[0]) and len(args) >= 2 and callable(args[1]):
        value, fn, predicate = args[0], args[1], args[2]
        return fn(value) if predicate(value) else value
    fn, predicate, *rest = args # type: ignore
    return fn(*rest, **kwargs) if predicate(*rest, **kwargs) else None


def apply_catch(*args, default=None, exceptions=Exception, **kwargs):
    """Apply a function while catching `exceptions`.

    Preferred: apply_catch(value, fn, exceptions | (exceptions,), default=None)
    Legacy:    apply_catch(fn, *args, default=None, exceptions=Exception)

    Args:
        *args: The arguments to apply the function to.
        **kwargs: The keyword arguments to apply the function with.

    Returns:
        The result of the function, or None if the predicate is false.
    
    Examples:
        >>> apply_catch(1, lambda x: x + 1, lambda x: x > 0)
        2
    """
    if isinstance(exceptions, (list, set)):
        exceptions = tuple(exceptions)
    if not isinstance(exceptions, tuple) and isinstance(exceptions, type):
        exc_types = exceptions
    else:
        try:
            exc_types = tuple(exceptions)  # type: ignore
        except TypeError:
            exc_types = Exception

    # value-first
    if args and not callable(args[0]) and len(args) >= 2 and callable(args[1]):
        value, fn = args[0], args[1]
        try:
            return fn(value)
        except exc_types:
            return value if default is None else default

    # legacy
    fn, *fargs = args # type: ignore
    try:
        return fn(*fargs, **kwargs)  # type: ignore
    except exc_types:
        return default
