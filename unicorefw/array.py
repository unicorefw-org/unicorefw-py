"""
File: unicorefw/array.py
Array manipulation functions for UniCoreFW.

This module contains functions for working with arrays and list-like structures.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""

import random as random_module
import builtins  # Import Python's built-ins to avoid recursion
import bisect
import re
from typing import (
    Iterable,
    List,
    Tuple,
    Callable,
    TypeVar,
    Union,
    Any,
    Optional,
    Dict,
    Set,
)
from .supporter import (
    _flatten
)

T = TypeVar("T")
U = TypeVar("U")
K = TypeVar("K")
V = TypeVar("V")


def map(array: List[T], func: Callable[[T], U]) -> List[U]:
    """
    Apply a function to each element of an array and return a new array.

    Args:
        array: The array to map
        func: The function to apply to each element

    Returns:
        A new array with the results of applying func to each element

    Examples:
        >>> map([1, 2, 3], lambda x: x * 2)
        [2, 4, 6]
    """
    return [func(x) for x in array]


def reduce(array: List[T], func: Callable[[U, T], U], initial: Optional[U] = None) -> U:
    """
    Reduce an array to a single value using a function.

    Args:
        array: The array to reduce
        func: A function that takes two arguments (accumulator, current value)
        initial: The initial value for the accumulator (optional)

    Returns:
        The reduced value

    Examples:
        >>> reduce([1, 2, 3], lambda x, y: x + y, 0)
        6
    """
    result = initial
    for x in array:
        if result is None:
            result = x
        else:
            result = func(result, x)  # type: ignore
    return result  # type: ignore


def find(array: List[T], func: Callable[[T], bool]) -> Optional[T]:
    """
    Find the first element in the array that matches the predicate function.

    Args:
        array: The array to search
        func: A predicate function that returns True for a match

    Returns:
        The first matching element, or None if not found

    Raises:
        TypeError: If array is not iterable or func is not callable

    Examples:
        >>> find([1, 2, 3], lambda x: x % 2 == 0)
        2
    """
    # Input validation
    if not hasattr(array, "__iter__"):
        raise TypeError("The 'array' parameter must be iterable.")
    if not callable(func):
        raise TypeError("The 'func' parameter must be callable.")

    for x in array:
        try:
            if func(x):
                return x
        except Exception:
            # Handle exceptions securely
            # Optionally log the exception without exposing sensitive information
            continue  # Skip elements that cause exceptions
    return None


def uniq(array: List[T]) -> List[T]:
    """
    Remove duplicates from an array.

    Args:
        array: The array to deduplicate

    Returns:
        A new array with duplicates removed

    Examples:
        >>> uniq([1, 2, 3, 2, 1])
        [1, 2, 3]
    """
    seen = []
    result: List[T] = []
    for x in array:
        if x not in seen:
            seen.append(x)
            result.append(x)
    return result


def first(*args, **kwargs) -> Union[T, List[T], None]:
    """
    Return the first element of an array or the first `n` elements if specified.

    Args:
        *args: The array or array elements, and possibly `n`
        **kwargs: Optional keyword argument 'n'

    Returns:
        The first element or first `n` elements of the array

    Examples:
        >>> first([1, 2, 3], 1)
        1
    """
    n = kwargs.get("n", None)

    # If no arguments are provided, return None or an empty list based on `n`
    if len(args) == 0:
        return None if n is None else []

    # Check if the last argument is an integer and can be considered as `n`
    if n is None and isinstance(args[-1], int):
        n = args[-1]
        args = args[:-1]

    # If the first argument is None or an empty list, handle cases accordingly
    if (
        len(args) == 0
        or args[0] is None
        or (len(args) == 1 and isinstance(args[0], (list, tuple)) and not args[0])
    ):
        return None if n is None else []

    # If the first argument is a list or tuple, treat it as the array
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        array = args[0]
    else:
        # Treat all positional arguments as the array elements
        array = list(args)

    # Handle the case where `n` is not provided
    if n is None:
        return array[0] if array else None

    # Validate `n` and handle cases where `n` <= 0
    if not isinstance(n, int) or n <= 0:
        return []

    # Return the first `n` elements, or the whole array if `n` exceeds the array length
    if n == 1:
        return array[0] if array else None

    return array[:n]  # type: ignore


def last(*args, **kwargs) -> Union[T, List[T], None]:
    """
    Return the last element of an array or the last `n` elements if specified.

    Args:
        *args: The array or array elements
        **kwargs: Optional keyword argument 'n'

    Returns:
        The last element or last `n` elements of the array

    Examples:
        >>> last([1, 2, 3], 1)
        3
    """
    n = kwargs.get("n", None)

    if not args:
        return None if n is None else []

    if len(args) == 1:
        array = args[0]
        if array is None or (isinstance(array, (list, tuple)) and not array):
            return None if n is None else []
        elif not isinstance(array, (list, tuple)):
            array = [array]  # Single element treated as a list
    elif (
        len(args) == 2
        and isinstance(args[0], (list, tuple))
        and isinstance(args[1], int)
        and n is None
    ):
        array = args[0]
        n = args[1]
    else:
        array = list(args)

    if n is None:
        return array[-1] if array else None

    if not isinstance(n, int) or n <= 0:
        return []

    return array[-n:]  # type: ignore


def compact(array: List[Any]) -> List[Any]:  # type: ignore
    """
    Remove falsey values from an array.

    Args:
        array: The array to compact

    Returns:
        A new array with falsey values removed

    Examples:
        >>> compact([0, 1, False, 2, '', 3, None, [], 4])
        [1, 2, 3, 4]
    """
    return [x for x in array if x]


def without(array: List[T], *values) -> List[T]:
    """
    Return an array excluding all provided values.

    Args:
        array: The array to filter
        *values: The values to exclude

    Returns:
        A new array with specified values removed

    Examples:
        >>> without([1, 2, 3], 2)
        [1, 3]
    """
    return [x for x in array if x not in values]


def pluck(array: List[dict], key: str) -> List[Any]:
    """
    Extract a list of property values from an array of objects.

    Args:
        array: An array of objects
        key: The property key to extract

    Returns:
        A list of the property values

    Examples:
        >>> pluck([{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], 'a')
        [1, 3]
    """
    return [
        obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)
        for obj in array
    ]


def shuffle(array: List[T]) -> List[T]:
    """
    Randomly shuffle the values in an array.

    Args:
        array: The array to shuffle

    Returns:
        A new shuffled array

    Examples:
        >>> shuffle([1, 2, 3, 4, 5])
        [3, 1, 5, 2, 4]
    """
    # Use the Fisher-Yates shuffle algorithm
    array_copy = list(array)
    for i in builtins.range(len(array_copy) - 1, 0, -1):
        j = random_module.randint(0, i)
        array_copy[i], array_copy[j] = array_copy[j], array_copy[i]
    return array_copy


def zip(*arrays) -> List[Tuple]:
    """
    Combine multiple arrays into an array of tuples.

    Args:
        *arrays: The arrays to zip

    Returns:
        A list of tuples

    Examples:
        >>> zip(['a', 'b', 'c'], [1, 2, 3])
        [('a', 1), ('b', 2), ('c', 3)]
    """
    return list(builtins.zip(*arrays))

def unzip(
    array_of_tuples: List[Tuple[Any, ...]],
    as_lists: bool = True
) -> List[Union[Tuple[Any, ...], List[Any]]]:
    """
    Reverse the zip operation by separating tuples into grouped sequences.

    By default, returns a list of tuples. If `as_lists=True`, returns a list of lists.

    Args:
        array_of_tuples: A list of tuples to unzip. Tuples must all be the same size.
        as_lists: Whether to return each group as a list (True) or tuple (False).

    Returns:
        A list where each element is a tuple (or list, if as_lists=True) containing
        the i-th elements of each input tuple.

    Examples:
        >>> data = [('a', 1), ('b', 2), ('c', 3)]
        >>> unzip(data)
        [('a', 'b', 'c'), (1, 2, 3)]
        >>> unzip(data, as_lists=True)
        [['a', 'b', 'c'], [1, 2, 3]]

        >>> records = [("moe", 30, True), ("larry", 40, False), ("curly", 35, True)]
        >>> unzip(records)
        [('moe', 'larry', 'curly'), (30, 40, 35), (True, False, True)]
        >>> unzip(records, as_lists=True)
        [['moe', 'larry', 'curly'], [30, 40, 35], [True, False, True]]

    Raises:
        ValueError: If `array_of_tuples` is empty or contains tuples of varying lengths.
    """
    if not array_of_tuples:
        return []

    # Validate uniform tuple lengths
    expected_len = len(array_of_tuples[0])
    for idx, tpl in enumerate(array_of_tuples):
        if len(tpl) != expected_len:
            raise ValueError(
                f"All tuples must have the same length: tuple at index {idx} has length {len(tpl)}, expected {expected_len}"
            )

   
    groups = list(zip(*array_of_tuples))
    if as_lists:
        return [list(group) for group in groups]
    return groups # type: ignore

def unzip_(array_of_tuples: List[Tuple[Any, ...]]):
    return unzip(array_of_tuples, as_lists=False)

def partition(array: List[T], predicate: Callable[[T], bool]) -> List[List[T]]:
    """
    Partition an array into two lists based on a predicate.

    Args:
        array: The array to partition
        predicate: A function that returns True or False

    Returns:
        A list of two lists [truthy, falsy]

    Examples:
        >>> partition([1, 2, 3], lambda x: x % 2 == 0)
        [[2], [1, 3]]
    """
    truthy = [item for item in array if predicate(item)]
    falsy = [item for item in array if not predicate(item)]
    return [truthy, falsy]


def last_index_of(array: List[T], value: T, from_index: Optional[int] = None) -> int:
    """
    Gets the index at which the last occurrence of value is found in the array.

    Args:
        array: List to search.
        value: Value to search for.
        from_index: Index to search from.

    Returns:
        Index of found item or -1 if not found.

    Examples:
        >>> last_index_of([1, 2, 2, 4], 2)
        2
        >>> last_index_of([1, 2, 2, 4], 2, from_index=1)
        1
    """
    length = len(array)
    if length == 0:
        return -1
    if from_index is None:
        idx = length - 1
    else:
        idx = from_index if from_index >= 0 else length + from_index
        idx = min(idx, length - 1)
    for i in builtins.range(idx, -1, -1):
        if array[i] == value:
            return i
    return -1


def chunk(array: List[T], size: int = 1) -> List[List[T]]:
    """
    Split an array into chunks of specified size.

    Args:
        array: The array to chunk
        size: The chunk size

    Returns:
        A list of chunks

    Examples:
        >>> chunk([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    if size <= 0:
        return []
    return [array[i : i + size] for i in range(0, len(array), size)]


def initial(array: List[T], n: int = 1) -> List[T]:
    """
    Return all elements except the last n elements.

    Args:
        array: The array
        n: Number of elements to exclude from the end

    Returns:
        A new array without the last n elements

    Examples:
        >>> initial([1, 2, 3], 1)
        [1, 2]
    """
    return array[:-n] if n < len(array) else []


def rest(array: List[T], n: int = 1) -> List[T]:
    """
    Return all elements except the first n elements.

    Args:
        array: The array
        n: Number of elements to exclude from the start

    Returns:
        A new array without the first n elements

    Examples:
        >>> rest([1, 2, 3], 1)
        [2, 3]
    """
    return array[n:]


def contains(array: List[T], value: T) -> bool:
    """
    Check if a value is present in the array.

    Args:
        array: The array to search
        value: The value to find

    Returns:
        True if the value is in the array, False otherwise

    Examples:
        >>> contains([1, 2, 3], 2)
        True
    """
    return value in array

def flatten(array, depth=float("inf")):
    """
    Efficiently flatten a nested list structure to the given depth using an iterative approach.

    Args:
        array: A list to flatten (supports nested lists)
        depth: Maximum depth to flatten. Use `True` for shallow (depth=1), float('inf') for full flatten.

    Returns:
        Flattened list.

    Examples:
        >>> flatten([[1], [2, [3]], [[4]]], 2)
        [1, 2, 3, [4]]
    """
    return _flatten(array, depth)


def reject(array: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """
    Return items that do not match the predicate.

    Args:
        array: The array to filter
        predicate: A function that returns True for items to reject

    Returns:
        A new array with rejected items removed

    Examples:
        >>> reject([1, 2, 3], lambda x: x % 2 == 0)
        [1, 3]
    """
    return [x for x in array if not predicate(x)]


def filter(array: List[T], func: Callable[[T], bool]) -> List[T]:
    """
    Filter elements in array based on func predicate.

    Args:
        array: The array to filter
        func: A function that returns True for items to keep

    Returns:
        A new array with only matching items

    Examples:
        >>> filter([1, 2, 3], lambda x: x % 2 == 0)
        [2]
    """
    return [x for x in array if func(x)]


def sample(array: List[T], n: int = 1) -> Union[List[T], T]:
    """
    Return a random sample from an array.

    Args:
        array: The array to sample from
        n: Number of items to sample

    Returns:
        A list of sampled items or a single item if n=1

    Examples:
        >>> sample([1, 2, 3], 2)
        [1, 3]
    """
    if n <= 0:
        return []

    from random import sample as random_sample

    result = random_sample(array, min(n, len(array)))

    if n == 1 and len(result) == 1:
        return result[0]
    return result


def index_by(array: List[dict], key_func: Union[str, Callable]) -> dict:
    """
    Index the array by a specific key or a function.

    Args:
        array: An array of objects
        key_func: A string key or a function that returns a key

    Returns:
        A dictionary indexed by the key or function result

    Examples:
        >>> index_by([{'id': 1}, {'id': 2}], 'id')
        {1: {'id': 1}, 2: {'id': 2}}
    """
    if isinstance(key_func, str):
        return {item[key_func]: item for item in array if key_func in item}
    else:
        return {key_func(item): item for item in array}


def count_by(array: List[T], key_func: Callable[[T], K]) -> dict:
    """
    Count instances in an array based on a function's result.

    Args:
        array: The array to count
        key_func: A function that returns a grouping key

    Returns:
        A dictionary of counts by key

    Raises:
        TypeError: If array is not iterable or key_func is not callable

    Examples:
        >>> count_by([1, 2, 3], lambda x: x % 2)
        {0: 2, 1: 1}
    """
    if not hasattr(array, "__iter__"):
        raise TypeError("The 'array' parameter must be iterable.")
    if not callable(key_func):
        raise TypeError("The 'key_func' parameter must be callable.")

    counts = {}
    for item in array:
        try:
            key = key_func(item)
            counts[key] = counts.get(key, 0) + 1
        except Exception:
            # Handle exceptions securely
            # Optionally log the exception without exposing sensitive information
            continue  # Skip elements that cause exceptions

    return counts


def difference(array: List[T], *others) -> List[T]:
    """
    Return values from the first array not present in others.

    Args:
        array: The source array
        *others: Other arrays to check against

    Returns:
        An array of unique values in the first array but not in others

    Examples:
        >>> difference([1, 2, 3], [2, 3, 4])
        [1]
    """
    other_elements = set().union(*others)
    return [x for x in array if x not in other_elements]


def union(*arrays: List[T], iteratee: Optional[Callable[[T], Any]] = None) -> List[T]:
    # simple union
    """
    Creates a new list that contains unique elements from all provided arrays.

    Args:
        arrays: Variable number of lists from which to compute the union.
        iteratee: An optional function that is applied to each element to generate
                  the criterion by which uniqueness is computed.

    Returns:
        A list of unique elements present in any of the input arrays in the order
        they first appear.

    Examples:
        >>> union([1, 2], [2, 3], [3, 4])
        [1, 2, 3, 4]
    """

    result: List[T] = []
    for arr in arrays:
        for x in arr:
            if x not in result:
                result.append(x)
    return result


def sort_by(array: List[T], key_func: Callable[[T], Any]) -> List[T]:
    """
    Sort an array by a function or key.

    Args:
        array: The array to sort
        key_func: A function that returns a comparable value

    Returns:
        A new sorted array

    Examples:
        >>> sort_by([1, 2, 3], lambda x: -x)
        [3, 2, 1]
    """
    return sorted(array, key=key_func)


def group_by(array: List[T], key_func: Callable[[T], K]) -> dict:
    """
    Group array elements by the result of a function.

    Args:
        array: The array to group
        key_func: A function that returns a grouping key

    Returns:
        A dictionary with keys from key_func and arrays as values

    Raises:
        TypeError: If array is not iterable or key_func is not callable

    Examples:
        >>> group_by([1, 2, 3], lambda x: x % 2)
        {0: [2], 1: [1, 3]}
    """
    if not hasattr(array, "__iter__"):
        raise TypeError("The 'array' parameter must be iterable.")
    if not callable(key_func):
        raise TypeError("The 'key_func' parameter must be callable.")

    grouped = {}
    for item in array:
        try:
            key = key_func(item)
            grouped.setdefault(key, []).append(item)
        except Exception:
            # Handle exceptions securely
            # Optionally log the exception without exposing sensitive information
            continue  # Skip elements that cause exceptions

    return grouped


def range(start: int, stop: Optional[int] = None, step: int = 1) -> List[int]:
    """
    Generate an array of numbers in a range.

    Args:
        start: Start number or stop if stop is None
        stop: End number (exclusive)
        step: Step between numbers

    Returns:
        A list of numbers

    Examples:
        >>> range(5)
        [0, 1, 2, 3, 4]
        >>> range(2, 5)
        [2, 3, 4]
    """
    if stop is None:
        start, stop = 0, start
    return list(builtins.range(start, stop, step))


def max_value(
    array: List[T], key_func: Optional[Callable[[T], Any]] = None
) -> Optional[T]:
    """
    Return the maximum value in the array, based on an optional key function.
    Returns None if the array is empty.

    Examples:
        >>> max_value([1, 2, 3])
        3
    """
    if not array:
        return None
    if key_func:
        return builtins.max(array, key=key_func)
    return builtins.max(array)  # type: ignore


def min_value(
    array: List[T], key_func: Optional[Callable[[T], Any]] = None
) -> Optional[T]:
    """
    Return the minimum value in the array, based on an optional key function.
    Returns None if the array is empty.

    Args:
        array: The array to search.
        key_func: Optional function to determine the comparison key.

    Returns:
        The minimum value or None if the array is empty.

    Examples:
        >>> min_value([3, 1, 2])
        1
        >>> min_value([{'a': 3}, {'a': 1}], key_func=lambda x: x['a'])
        {'a': 1}
    """

    if not array:
        return None
    if key_func:
        return builtins.min(array, key=key_func)
    return builtins.min(array)  # type: ignore


def find_median_sorted_arrays(nums1: List[float], nums2: List[float]) -> float:
    """
    Find the median of two sorted arrays using binary search.

    Args:
        nums1: First sorted array
        nums2: Second sorted array

    Returns:
        The median value

    Examples:
        >>> find_median_sorted_arrays([1.0, 2.0], [3.0, 4.0])
        2.5
    """
    # Ensure nums1 is the smaller array for binary search efficiency
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1

    m, n = len(nums1), len(nums2)
    total_length = m + n
    half_length = (total_length + 1) // 2  # For handling both odd/even cases

    left, right = 0, m

    while left <= right:
        partition1 = (left + right) // 2
        partition2 = half_length - partition1

        maxLeft1 = float("-inf") if partition1 == 0 else nums1[partition1 - 1]
        minRight1 = float("inf") if partition1 == m else nums1[partition1]

        maxLeft2 = float("-inf") if partition2 == 0 else nums2[partition2 - 1]
        minRight2 = float("inf") if partition2 == n else nums2[partition2]

        # Check if we've partitioned correctly
        if maxLeft1 <= minRight2 and maxLeft2 <= minRight1:
            # If odd, return the max of the left halves
            if total_length % 2 == 1:
                return max(maxLeft1, maxLeft2)
            # If even, return the average of the two middle values
            return (max(maxLeft1, maxLeft2) + min(minRight1, minRight2)) / 2.0
        elif maxLeft1 > minRight2:
            # Move towards left in nums1
            right = partition1 - 1
        else:
            # Move towards right in nums1
            left = partition1 + 1

    return 0

####################################################################################
#  Extended Array Functions
####################################################################################
def difference_by(array: List[T], *args) -> List[T]:
    """
    Creates an array of values not included in the other given arrays
    using SameValueZero for equality comparisons.

    Args:
        array (List[T]): The array to inspect.
        values (List[T]): The values to exclude.
        iteratee (Optional[Callable[[T], Any]]): The iteratee to transform values.

    Returns:
        List[T]: Returns the new array of values not included in the other given arrays.

    Examples:
        >>> difference_by([2.1, 1.2, 2.3], [2.3, 3.4], key=lambda x: round(x))
        [1.2]
    """
    if not args:
        return list(array)
    # last arg may be iteratee
    iteratee = args[-1]
    if callable(iteratee) or isinstance(iteratee, str):
        values = [] if len(args) == 1 else args[0]
    else:
        iteratee = None
        values = args[0]
    if iteratee is None:

        def key(x):  # type: ignore
            return x
    elif isinstance(iteratee, str):

        def key(x):
            return (
                x.get(iteratee) if isinstance(x, dict) else getattr(x, iteratee, None)
            )
    else:
        key = iteratee  # type: ignore
    other_keys = {key(v) for v in (values or [])}
    return [item for item in array if key(item) not in other_keys]


def difference_with(array: List[T], *args) -> List[T]:
    """
    Creates an array of values not included in the other given arrays
    using `comparator` for equality comparisons.

    Args:
        array (List[T]): The array to inspect.
        values (List[T]): The values to exclude.
        comparator (Optional[Callable[[T, T], bool]]): The comparator to transform values.

    Returns:
        List[T]: Returns the new array of values not included in the other given arrays.

    Examples:
        >>> difference_with([2.1, 1.2, 2.3], [2.3, 3.4], lambda a, b: round(a, 1) == round(b, 1))
        [1.2]
    """
    if not args:
        return list(array)
    comparator = args[-1] if callable(args[-1]) else None  # type: ignore
    values = args[0] if comparator else args[0]
    if comparator is None:

        def comparator(a, b):
            return a == b  # type: ignore

    result: List[T] = []
    for item in array:
        if not any(comparator(item, v) for v in values):
            result.append(item)
    return result


def drop(array: List[T], n: int = 1) -> List[T]:
    """
    Creates a slice of `array` with `n` elements dropped from the beginning.

    Args:
        array: List to process.
        n: Number of elements to drop. Defaults to ``1``.

    Returns:
        Dropped list.

    Examples:
        >>> drop([1, 2, 3, 4], 2)
        [3, 4]
    """
    return array[n:]


def drop_right(array: List[T], n: int = 1) -> List[T]:
    """
    Creates a slice of `array` with `n` elements dropped from the end.

    Args:
        array: List to process.
        n: Number of elements to drop. Defaults to ``1``.

    Returns:
        Dropped list.

    Examples:
        >>> drop_right([1, 2, 3, 4], 2)
        [1, 2]
    """
    return array[:-n] if n else list(array)


def drop_while(array: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """
    Creates a slice of `array` excluding elements dropped from the beginning. Elements are dropped
    until `predicate` returns falsey. The predicate is invoked with three arguments: (value, index, array).

    Args:
        array: List to process.
        predicate: Function invoked per iteration.

    Returns:
        Dropped list.

    Examples:
        >>> drop_while([1, 2, 3, 4], lambda x: x < 3)
        [3, 4]
    """
    for idx, x in enumerate(array):
        if not predicate(x):
            return array[idx:]
    return []


def drop_right_while(array: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """
    Creates a slice of `array` excluding elements dropped from the end. Elements are dropped until
    `predicate` returns falsey. The predicate is invoked with three arguments: (value, index, array).

    Args:
        array: List to process.
        predicate: Function invoked per iteration.

    Returns:
        Dropped list.

    Examples:
        >>> drop_right_while([1, 2, 3, 4], lambda x: x >= 3)
        [1, 2]
    """
    for idx in range(len(array) - 1, -1, -1):
        if not predicate(array[idx]):
            return array[: idx + 1]
    return []


def duplicates(array: List[T], iteratee: Callable[[T], Any] = lambda x: x) -> List[T]:
    """
    Creates an array of unique elements from the first occurrence of each value in `array`.

    Args:
        array: List to process.
        iteratee: Function invoked per iteration.

    Returns:
        List of duplicates.

    Examples:
        >>> duplicates([0, 1, 3, 2, 3, 1])
        [3, 1]
    """
    seen: set = set()
    dup_set: set = set()
    result: List[T] = []
    for item in array:
        key = iteratee(item)
        if key in seen and key not in dup_set:
            dup_set.add(key)
            result.append(item)
        seen.add(key)
    return result


def fill(
    array: List[T], value: T, start: int = 0, end: Optional[int] = None
) -> List[T]:
    """
    Fills elements of array with value from start up to, but not including, end.

    Args:
        array: List to fill.
        value: Value to fill with.
        start: Index to start filling. Defaults to ``0``.
        end: Index to end filling. Defaults to ``len(array)``.

    Returns:
        Filled array.

    Examples:
        >>> fill([1, 2, 3, 4, 5], 0)
        [0, 0, 0, 0, 0]
        >>> fill([1, 2, 3, 4, 5], 0, 1, 3)
        [1, 0, 0, 4, 5]
        >>> fill([1, 2, 3, 4, 5], 0, 0, 100)
        [0, 0, 0, 0, 0]

    Warning:
        array is modified in place.
    """
    length = len(array)
    if length == 0:
        return array
    s = start if start >= 0 else max(length + start, 0)
    e = end if end is not None else length
    e = e if e >= 0 else max(length + e, 0)
    s = min(max(s, 0), length)
    e = min(max(e, 0), length)
    for i in builtins.range(s, e):
        array[i] = value
    return array


def find_index(
    array: List[T], filter_by: Union[Callable[[T], bool], Dict[str, Any], Any]
) -> int:
    """
    Gets the index at which the first occurrence of value is found.

    Args:
        array: List to search.
        filter_by: Value to search for.

    Returns:
        Index of the matched value, otherwise -1.

    Examples:
        >>> find_index([1, 2, 3, 4, 5], 3)
        2
        >>> find_index([1, 2, 3, 4, 5], 6)
        -1
    """
    if callable(filter_by):
        predicate = filter_by  # type: ignore
    elif isinstance(filter_by, dict):

        def predicate(x):  # type: ignore
            return all(x.get(k) == v for k, v in filter_by.items())  # type: ignore
    else:

        def predicate(x):
            return x == filter_by  # type: ignore

    for idx, item in enumerate(array):
        try:
            if predicate(item):
                return idx
        except Exception:
            continue
    return -1


def find_last_index(
    array: List[T], filter_by: Union[Callable[[T], bool], Dict[str, Any], Any]
) -> int:
    """
    Gets the index at which the last occurrence of value is found.

    Args:
        array: List to search.
        filter_by: Value to search for.

    Returns:
        Index of the matched value, otherwise -1.

    Examples:
        >>> find_last_index([1, 2, 3, 4, 5], 3)
        2
        >>> find_last_index([1, 2, 3, 4, 5], 6)
        -1
    """
    if callable(filter_by):
        predicate = filter_by  # type: ignore
    elif isinstance(filter_by, dict):

        def predicate(x):  # type: ignore
            return all(x.get(k) == v for k, v in filter_by.items())  # type: ignore
    else:

        def predicate(x):
            return x == filter_by  # type: ignore

    for idx in builtins.range(len(array) - 1, -1, -1):
        try:
            if predicate(array[idx]):
                return idx
        except Exception:
            continue
    return -1


def flatten_deep(array: Any) -> List[Any]:
    """
    Recursively flattens array.

    Args:
        array: List to flatten.

    Returns:
        Flattened list.

    Examples:
        >>> flatten_deep([[1], [2, [3]], [[4]]])
        [1, 2, 3, 4]
    """
    return flatten(array, float("inf"))  # type: ignore


def flatten_depth(array: Any, depth: int = 1) -> List[Any]:
    """
    Recursively flattens array up to the specified depth.

    Args:
        array: List to flatten.
        depth: How deep to flatten the array.

    Returns:
        Flattened list.

    Examples:
        >>> flatten_depth([[1], [2, [3]], [[4]]], 2)
        [1, 2, 3, [4]]
    """
    return flatten(array, depth)


def from_pairs(pairs: List[Tuple[K, V]]) -> Dict[K, V]:
    """
    Converts a list of [key, value] pairs into an object.

    Args:
        pairs: List of key-value pairs.

    Returns:
        Object with the given key-value pairs.

    Examples:
        >>> from_pairs([["a", 1], ["b", 2]]) == {"a": 1, "b": 2}
        True
    """
    return {k: v for k, v in pairs}


def head(array: List[T]) -> Optional[T]:
    """
    Returns the first element of the array, if it exists.

    Args:
        array: List from which to retrieve the first element.

    Returns:
        The first element of the list if it is not empty, otherwise None.

    Examples:
        >>> head([1, 2, 3])
        1
        >>> head([])
        None
    """

    return array[0] if array else None


def index_of(array: List[T], value: T, from_index: int = 0) -> int:
    """
    Gets the index at which the first occurrence of value is found.

    Args:
        array: List to search.
        value: Value to search for.
        from_index: Index to search from.

    Returns:
        Index of found item or -1 if not found.

    Examples:
        >>> index_of([1, 2, 3, 4], 2)
        1
        >>> index_of([2, 1, 2, 3], 2, from_index=1)
        2
    """
    length = len(array)
    start = from_index if from_index >= 0 else max(length + from_index, 0)
    for i in builtins.range(start, length):
        if array[i] == value:
            return i
    return -1


def interleave(*arrays: List[T]) -> List[T]:
    """
    Merge multiple lists into a single list by inserting the next element of each list by sequential
    round-robin into the new list.

    Args:
        arrays: Lists to interleave.

    Returns:
        Interleaved list.

    Examples:
        >>> interleave([1, 2, 3], [4, 5, 6], [7, 8, 9])
        [1, 4, 7, 2, 5, 8, 3, 6, 9]
    """
    result: List[T] = []
    max_len = max((len(arr) for arr in arrays), default=0)
    for i in builtins.range(max_len):
        for arr in arrays:
            if i < len(arr):
                result.append(arr[i])
    return result


def intersection_with(array: List[T], *args) -> List[T]:
    """
    Like intersection but accepts a comparator which is invoked to compare the elements of all arrays.
    The order and references of result values are determined by the first array. The comparator is invoked with two arguments: ``(arr_val, oth_val)``.

    Args:
        array: The array to find the intersection of.
        *args: Lists to check for intersection with `array`.

    Returns:
        Intersection of provided lists.

    Examples:
        >>> array = ["apple", "banana", "pear"]
        >>> others = (["avocado", "pumpkin"], ["peach"])
        >>> comparator = lambda a, b: a[0] == b[0]
        >>> intersection_with(array, *others, comparator=comparator)
        ['pear']
    """
    # last arg may be comparator
    comparator = None
    arrays: List[List[T]] = []
    if args and (callable(args[-1]) or args[-1] is None):
        comparator = args[-1]
        arrays = list(args[:-1])  # type: ignore
    else:
        arrays = list(args)  # type: ignore
    if not arrays:
        return array.copy()
    cmp = comparator if callable(comparator) else (lambda a, b: a == b)
    result: List[T] = []
    for x in array:
        if any(cmp(x, y) for y in result):
            continue
        if all(any(cmp(x, y) for y in arr) for arr in arrays):
            result.append(x)
    return result


def intersperse(array: List[T], sep: T) -> List[T]:
    """
    Insert a separating element between the elements of `array`.

    Args:
        array: List to intersperse.
        sep: Element to insert.

    Returns:
        Interspersed list.

    Examples:
        >>> intersperse([1, [2], [3], 4], "x")
        [1, 'x', [2], 'x', [3], 'x', 4]
    """
    result: List[T] = []
    for idx, item in enumerate(array):
        if idx:
            result.append(sep)
        result.append(item)
    return result


def mapcat(array: List[T], func: Callable[[T, int], List[U]]) -> List[U]:
    """
    Map over an array, concatenating the results.

    Args:
        array: The array to map over.
        func: A function that takes an element and its index, and returns an
            iterable of values to be concatenated into the result.

    Returns:
        A new array with the concatenated results.

    Examples:
        >>> mapcat([1, 2, 3], lambda x, _: [x, x])
        [1, 1, 2, 2, 3, 3]
    """

    result: List[U] = []
    for idx, x in enumerate(array):
        res = func(x, idx)  # type: ignore
        result.extend(res or [])
    return result


def nth(array: List[T], index: int) -> Optional[T]:
    """
    Gets the element at index n of array.

    Args:
        array: List passed in by the user.
        index: Index of element to return.

    Returns:
        Returns the element at :attr:`index`.

    Examples:
        >>> nth([1, 2, 3, 4], 0)
        1
        >>> nth([3, 4, 5, 6], 2)
        5
        >>> nth([11, 22, 33], -1)
        33
        >>> nth([11, 22, 33])
        11
    """

    length = len(array)
    if index < 0:
        idx = length + index
        if 0 <= idx < length:
            return array[idx]
    else:
        if 0 <= index < length:
            return array[index]
    return None


def pull(array: List[T], *values: T) -> List[T]:
    """
    Removes all provided values from the given array.

    Args:
        array: List to pull from.
        values: Values to remove.

    Returns:
        Modified `array`.

    Warning:
        `array` is modified in place.

    Examples:

        >>> pull([1, 2, 2, 3, 3, 4], 2, 3)
        [1, 4]
    """
    return [x for x in array if x not in values]


def pull_all(array: List[T], values: List[T]) -> List[T]:
    """
    Removes all provided values from the given array.

    Args:
        array: The array to modify.
        values: The values to remove.

    Returns:
        A new list with the specified values removed.

    Examples:
        >>> pull_all([1, 2, 2, 3, 3, 4], [2, 3])
        [1, 4]
    """
    return [x for x in array if x not in values]


def pull_all_by(
    array: List[T], values: List[T], iteratee: Optional[Callable[[T], Any]] = None
) -> List[T]:
    """
    Removes all elements from array that have the same value as the result of calling
    the iteratee on each element of values. The iteratee is invoked with one argument:
    (value).

    Args:
        array: The array to modify.
        values: The values to remove.
        iteratee: The iteratee to transform values.

    Returns:
        A new list with the specified values removed.

    Examples:
        >>> pull_all_by([1, 2, 3], [2, 3], lambda x: x % 2)
        [1]
    """
    if iteratee is None:
        return [x for x in array if x not in values]
    keys = {iteratee(v) for v in values}
    return [x for x in array if iteratee(x) not in keys]


def pull_all_with(
    array: List[T], values: List[T], comparator: Optional[Callable[[T, T], bool]] = None
) -> List[T]:
    """
    Removes all elements from array that have the same value as the result of calling
    the comparator between the elements of array and values. The comparator is invoked
    with two arguments: (arr_val, oth_val).

    Args:
        array: The array to modify.
        values: The values to remove.
        comparator: The comparator to compare the elements of the arrays.

    Returns:
        A new list with the specified values removed.

    Examples:
        >>> pull_all_with([1, 2, 3], [2, 3], lambda a, b: a == b)
        [1]
    """
    if comparator is None:
        return [x for x in array if x not in values]
    return [x for x in array if not any(comparator(x, v) for v in values)]


def push(array: List[T], *values: T) -> List[T]:
    """
    Appends values to the end of an array.

    Args:
        array: The array to append to.
        *values: The values to append.

    Returns:
        The modified array.

    Examples:
        >>> push([1, 2], 3, 4)
        [1, 2, 3, 4]

    Note:
        This is a mutable operation on the array.
    """
    array.extend(values)
    return array

def shift(array: List[T]) -> Optional[T]:
    """
    Remove the first element of the array and return it.

    Args:
        array: The list to shift.

    Returns:
        The first element of the array if it is not empty, otherwise None.

    Examples:
        >>> array = [1, 2, 3]
        >>> item = shift(array)
        >>> item
        1
        >>> array
        [2, 3]
    """
    if array:
        return array.pop(0)
    return None


def sorted_index(array: List[T], value: T) -> int:
    """
    Determines the lowest index at which `value` should be inserted into `array`
    in order to maintain its sorted order.

    Args:
        array: A list of elements that are already sorted.
        value: The value to be inserted.

    Returns:
        The index at which `value` should be inserted to keep the array sorted.

    Examples:
        >>> sorted_index([1, 2, 2, 3, 4], 2)
        1
    """
    return bisect.bisect_left(array, value)  # type: ignore


def sorted_index_of(array: List[T], value: T) -> int:
    """
    Return the index of the first occurrence of `value` in `array` if `array` is sorted.

    Args:
        array: A list of elements that are already sorted.
        value: The value to search for.

    Returns:
        The index of the first occurrence of `value` in `array` if it exists, otherwise -1.

    Examples:
        >>> sorted_index_of([1, 2, 2, 3, 4], 2)
        1
    """
    try:
        return array.index(value)
    except ValueError:
        return -1


def sorted_last_index(array: List[T], value: T) -> int:
    """
    Determines the highest index at which `value` should be inserted into `array`
    in order to maintain its sorted order.

    Args:
        array: A list of elements that are already sorted.
        value: The value to be inserted.

    Returns:
        The index at which `value` should be inserted to keep the array sorted.

    Examples:
        >>> sorted_last_index([1, 2, 2, 3, 4], 2)
        3
    """
    return bisect.bisect_right(array, value)  # type: ignore


def sorted_last_index_of(array: List[T], value: T) -> int:
    """
    This method is like `sorted_last_index` except that it returns the index of the
    closest element to the supplied `value` in a sorted `array`. If `value` is not
    found, the index of the next closest element lower in value is returned.

    Args:
        array: Array to inspect.
        value: Value to evaluate.

    Returns:
        The index of the closest value to `value`. If `value` is not found, the
        index of the next closest element lower in value.

    Examples:
        >>> sorted_last_index_of([1, 2, 3, 4], 4.2)
        3
    """
    idx = array[::-1].index(value) if value in array else -1
    return len(array) - idx - 1 if idx >= 0 else -1


def splice(
    array: Union[List[T], str],
    start: int,
    delete_count: Optional[int] = None,
    *items: Any,
) -> Union[List[T], str]:
    # List handling
    """
    Modify the contents of `array` by inserting elements starting at index `start` and removing
    `delete_count` number of elements after.

    Args:
        array: List to splice.
        start: Start to splice at.
        delete_count: Number of items to remove starting at `start`. If ``None`` then all
            items after `start` are removed. Defaults to ``None``.
        items: Elements to insert starting at `start`. Each item is inserted in the order
            given.

    Returns:
        The removed elements of `array` or the spliced string.

    Warning:
        `array` is modified in place if ``list``.

    Examples:

        >>> array = [1, 2, 3, 4]
        >>> splice(array, 1)
        [2, 3, 4]
        >>> array
        [1]
        >>> array = [1, 2, 3, 4]
        >>> splice(array, 1, 2)
        [2, 3]
        >>> array
        [1, 4]
        >>> array = [1, 2, 3, 4]
        >>> splice(array, 1, 2, 0, 0)
        [2, 3]
        >>> array
        [1, 0, 0, 4]
    """
    if isinstance(array, list):
        length = len(array)
        s = start if start >= 0 else max(length + start, 0)
        d = delete_count if delete_count is not None else length - s
        removed = array[s : s + d]
        array[s : s + d] = list(items)
        return removed
    # String handling
    text: str = array  # type: ignore
    length = len(text)
    s = start if start >= 0 else max(length + start, 0)
    d = delete_count if delete_count is not None else length - s
    return text[:s] + "".join(items) + text[s + d :]


def split_at(array: List[T], index: int) -> List[List[T]]:
    """
    Splits an array into two sub-arrays at a specified index.

    Args:
        array: The list to split.
        index: The index at which to split the array.

    Returns:
        A list containing two sub-arrays. The first sub-array contains elements
        from the start of the array up to, but not including, the specified
        index. The second sub-array contains elements from the specified index
        to the end of the array.

    Examples:
        >>> split_at([1, 2, 3, 4], 2)
        [[1, 2], [3, 4]]
    """
    return [array[:index], array[index:]]


def tail(array: List[T]) -> List[T]:
    """
    Returns all but the first element of `array`.

    Args:
        array: List from which to retrieve all but the first element.

    Returns:
        A new list containing all but the first element of `array`.

    Examples:
        >>> tail([1, 2, 3])
        [2, 3]
    """
    return array[1:]


def take(array: List[T], n: int = 1) -> List[T]:
    """
    Creates a slice of `array` with `n` elements taken from the beginning.

    Args:
        array: List to process.
        n: Number of elements to take. Defaults to ``1``.

    Returns:
        Taken list.

    Examples:
        >>> take([1, 2, 3, 4], 2)
        [1, 2]
    """
    return array[:n]


def take_right(array: List[T], n: int = 1) -> List[T]:
    """
    Creates a slice of `array` with `n` elements taken from the end.

    Args:
        array: List to process.
        n: Number of elements to take. Defaults to ``1``.

    Returns:
        Taken list.

    Examples:
        >>> take_right([1, 2, 3, 4], 2)
        [3, 4]
    """
    return array[-n:] if n else []


def take_while(array: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """
    Creates a slice of `array` with elements taken from the beginning. Elements are taken until `predicate` returns falsey. The predicate is invoked with one argument: `(value)`.

    Args:
        array: List to process.
        predicate: Function invoked per iteration.

    Returns:
        Taken list.

    Examples:
        >>> take_while([1, 2, 3, 4], lambda x: x < 3)
        [1, 2]
    """
    result: List[T] = []
    for x in array:
        if predicate(x):
            result.append(x)
        else:
            break
    return result


def take_right_while(array: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """
    Creates a slice of `array` with elements taken from the end. Elements are taken until `predicate` returns falsey. The predicate is invoked with one argument: `(value)`.

    Args:
        array: List to process.
        predicate: Function invoked per iteration.

    Returns:
        Taken list.

    Examples:
        >>> take_right_while([1, 2, 3, 4], lambda x: x >= 3)
        [3, 4]
    """
    result: List[T] = []
    for x in reversed(array):
        if predicate(x):
            result.insert(0, x)
        else:
            break
    return result


def union_by(
    *arrays: List[T], iteratee: Optional[Callable[[T], Any]] = None
) -> List[T]:
    """
    Creates a new list that contains unique elements from all provided arrays,
    determined by the result of running each element through the iteratee function.

    Args:
        arrays: Variable number of lists from which to compute the union.
        iteratee: An optional function that is applied to each element to generate
                  the criterion by which uniqueness is computed.

    Returns:
        A list of unique elements present in any of the input arrays based on the iteratee.

    Examples:
        >>> union_by([1, 2, 3], [2, 3, 4], lambda x: x % 2)
        [1, 2]
    """
    args = list(arrays)
    if not arrays:
        return []
    # if last positional is callable and iteratee not provided
    if iteratee is None and callable(arrays[-1]):
        iteratee = arrays[-1]  # type: ignore
        args = args[:-1]
    fn = iteratee if callable(iteratee) else (lambda x: x)  # type: ignore
    seen = set()
    result: List[T] = []
    for arr in args:
        for x in arr:
            k = fn(x)
            if k not in seen:
                seen.add(k)
                result.append(x)
    return result


def union_with(array: List[T], *args) -> List[T]:
    """
    Creates a new list that contains unique elements from all provided arrays,
    determined by the comparator function.

    Args:
        arrays: Variable number of lists from which to compute the union.
        comparator: Optional function that is applied to compare the elements of the arrays.

    Returns:
        A list of unique elements present in any of the input arrays based on the comparator.

    Examples:
        >>> union_with([1, 2, 3], [2, 3, 4], lambda a, b: a == b)
        [1, 2, 3, 4]
    """

    comparator = None
    rest_arrays: List[List[T]] = []
    if args and callable(args[-1]):
        comparator = args[-1]
        rest_arrays = list(args[:-1])  # type: ignore
    else:
        rest_arrays = list(args)  # type: ignore
    result: List[T] = []
    cmp = comparator if callable(comparator) else (lambda a, b: a == b)
    for x in concat(array, *rest_arrays):
        if not any(cmp(x, y) for y in result):
            result.append(x)
    return result


def uniq_by(
    array: List[T], iteratee: Union[str, Callable[[T], Any], Dict[str, Any]]
) -> List[T]:
    # support dict, str, or callable
    """
    Creates a duplicate-value-free version of the array. Only the first occurrence of each value
    is kept. The order of result values is determined by the order they occur in the array.

    Args:
        array: List to process.
        iteratee: Function to transform the elements of the arrays, or a string or a dictionary
            that is used to filter the elements of the arrays. If a string is passed, it is used to
            access the given key of each element in the arrays. If a dictionary is passed, it is
            used to filter the elements of the arrays; the function will return ``True`` for
            elements that have the properties of the given object, else ``False``.

    Returns:
        Unique list.

    Examples:
        >>> uniq_by([1, 2, 3, 1, 2, 3], lambda val: val % 2)
        [1, 2]
    """
    if isinstance(iteratee, dict):
        pred = lambda x: all(x.get(k) == v for k, v in iteratee.items())  # noqa: E731
        key_fn = lambda x: bool(pred(x))  # noqa: E731
    elif isinstance(iteratee, str):

        def key_fn(x):
            return (
                x.get(iteratee) if isinstance(x, dict) else getattr(x, iteratee, None)
            )
    else:
        key_fn = iteratee # type: ignore
        
    seen = set()
    result: List[T] = []
    for x in array:
        k = key_fn(x)
        if k not in seen:
            seen.add(k)
            result.append(x)
    return result


def uniq_with(array: List[T], comparator: Callable[[T, T], bool]) -> List[T]:
    """
    Creates a duplicate-value-free version of the array. Only the first occurrence of each value
    is kept. The order of result values is determined by the order they occur in the array.

    Args:
        array: List to process.
        comparator: Function to compare the elements of the arrays.

    Returns:
        Unique list.

    Examples:
        >>> uniq_with([1, 2, 3, 1, 2, 3], lambda a, b: a == b)
        [1, 2, 3]
    """
    result: List[T] = []
    for item in array:
        if not any(comparator(item, x) for x in result):
            result.append(item)
    return result


def zip_object(keys: List[K], values: Optional[List[V]] = None) -> Dict[K, V]:
    """
    Creates an object composed of the given keys and values.
    If the `values` list is not provided, the `keys` list is treated as a list of key-value pairs.

    Args:
        keys: A list of keys or key-value pairs.
        values: A list of values to pair with the keys.

    Returns:
        An object with the key-value pairs.

    Examples:
        >>> zip_object(["a", "b"], [1, 2])
        {"a": 1, "b": 2}

        >>> zip_object([["a", 1], ["b", 2]])
        {"a": 1, "b": 2}
    """
    if values is None:
        return {k: v for k, v in keys}  # type: ignore
    return {k: v for k, v in builtins.zip(keys, values)}


def zip_object_deep(
    keys: List[Any], values: Optional[List[Any]] = None
) -> Dict[Any, Any]:
    """
    Creates a nested object from the given keys and values. If the `values` list is not provided, the `keys` list is treated as a list of key-value pairs.

    Args:
        keys: A list of keys or key-value pairs.
        values: A list of values to pair with the keys.

    Returns:
        A nested object with the key-value pairs.

    Examples:
        >>> zip_object_deep(["a.b.c", "a.b.d"], [1, 2])
        {"a": {"b": {"c": 1, "d": 2}}}
    """
    result: Dict[Any, Any] = {}
    # Build key-value pairs
    if values is None:
        pairs = keys  # type: ignore
    else:
        pairs = builtins.zip(keys, values)  # type: ignore
    for k, v in pairs:
        # parse path
        parts = re.findall(r"[^.\[\]]+", k)  # type: ignore
        node = result
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            # next part type
            if part.isdigit():
                idx = int(part)
                if not isinstance(node, list):
                    raise TypeError("Expected list at part %r" % part)
                while len(node) <= idx:
                    node.append({})
                if is_last:
                    node[idx] = v
                else:
                    if not isinstance(node[idx], dict):
                        node[idx] = {}
                    node = node[idx]
            else:
                if is_last:
                    node[part] = v  # type: ignore
                else:
                    # determine if next is index
                    nxt = parts[i + 1]
                    if nxt.isdigit():
                        if part not in node or not isinstance(node[part], list):
                            node[part] = []
                    else:
                        if part not in node or not isinstance(node[part], dict):
                            node[part] = {}
                    node = node[part]  # type: ignore
    return result


def concat(*arrays: Union[List[T], T]) -> List[T]:
    """
    Flattens an array of arrays or values into a single array.

    Args:
        *arrays: The arrays or values to flatten.

    Returns:
        A flattened list.

    Examples:
        >>> concat([1, 2, 3], [4, [5, 6]], 7, 8)
        [1, 2, 3, 4, 5, 6, 7, 8]
    """
    result: List[T] = []
    for arr in arrays:
        if isinstance(arr, (list, tuple)):
            result.extend(arr)  # type: ignore
        else:
            result.append(arr)  # type: ignore
    return result


def sorted_index_by(
    array: List[T], value: T, key: Union[str, Callable[[T], Any]]
) -> int:
    """
    Returns the index at which the value should be inserted to maintain sorted order.

    Args:
        array: The array to search.
        value: The value to search for.
        key: A function or string to extract the key from each element.

    Returns:
        The index at which the value should be inserted.

    Examples:
        >>> sorted_index_by([1, 2, 3], 4, lambda x: x)
        3
    """
    if isinstance(key, str):
        fn = lambda x: x.get(key) if isinstance(x, dict) else getattr(x, key, None)  # noqa: E731
    else:
        fn = key  # type: ignore
    keys = [fn(x) for x in array]
    return bisect.bisect_left(keys, fn(value))  # type: ignore


def sorted_last_index_by(
    array: List[T], value: T, key: Union[str, Callable[[T], Any]]
) -> int:
    """
    Returns the highest index at which `value` should be inserted into `array` in order to maintain
    the sort order, using a key function to extract the comparison key.

    Args:
        array: The array to inspect.
        value: The value to evaluate for insertion.
        key: A function or string to extract the key from each element.

    Returns:
        The index at which the value should be inserted to keep the array sorted.

    Examples:
        >>> sorted_last_index_by([{'x': 1}, {'x': 2}, {'x': 3}], {'x': 2}, 'x')
        2
    """

    if isinstance(key, str):
        fn = lambda x: x.get(key) if isinstance(x, dict) else getattr(x, key, None)  # noqa: E731
    else:
        fn = key  # type: ignore
    keys = [fn(x) for x in array]
    return bisect.bisect_right(keys, fn(value))  # type: ignore


def sorted_uniq(array: List[T]) -> List[T]:
    """
    Creates a duplicate-free version of an array, keeping only the first occurrence
    of each element, then sorted by the original elements.

    Args:
        array: The input array to process

    Returns:
        New array with unique elements sorted by the original element values

    Algorithm:
    1. Collect unique elements, keeping first occurrence
    2. Sort the unique elements by their original values
    3. Return the sorted unique array

    Security & Performance:
    - Input validation for safety
    - Efficient single-pass uniqueness detection
    - Direct sorting of original elements

    Examples:
        >>> sorted_uniq([1, 2, 3, 2, 1])
        [1, 2, 3]
    """
    seen = set()
    result: List[T] = []
    for x in sorted(array):  # type: ignore
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def sorted_uniq_by(array: List[Any], iteratee: Callable[[Any], Any]) -> List[Any]:
    """
    Creates a duplicate-free version of an array, keeping only the first occurrence
    of each element based on the iteratee function, then sorted by the original elements.

    Args:
        array: The input array to process
        iteratee: Function to compute the unique key for each element

    Returns:
        New array with unique elements (by iteratee) sorted by the original element values

    Algorithm:
    1. Collect unique elements by iteratee key, keeping first occurrence
    2. Sort the unique elements by their original values (not iteratee values)
    3. Return the sorted unique array

    Security & Performance:
    - Input validation for safety
    - Efficient single-pass uniqueness detection
    - Direct sorting of original elements

    Examples:
        >>> sorted_uniq_by([1, 2, 3, 2, 1], lambda x: x % 2)
        [1, 2]
    """
    if not array:
        return []

    if not callable(iteratee):
        raise TypeError("Iteratee must be callable")

    # Track seen keys and collect unique elements
    seen_keys: Set[Any] = set()
    unique_elements: List[Any] = []

    # First pass: collect unique elements (first occurrence only)
    for element in array:
        try:
            key = iteratee(element)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_elements.append(element)
        except (TypeError, AttributeError) as e:
            raise TypeError(f"Iteratee function failed on element {element}: {str(e)}")

    # Sort by the original elements themselves, not by iteratee values
    unique_elements.sort()

    return unique_elements


def intercalate(array: List[T], separator: List[T]) -> List[T]:
    """
    Creates a new list by intercalating a given list of elements with a separator value.

    Args:
        array: List of elements to intercalate.
        separator: List of separator values to insert between elements.

    Returns:
        New list with separator values inserted between elements.

    Examples:
        >>> intercalate([1, 2, 3], [4, 5, 6])
        [1, 4, 5, 6, 2, 4, 5, 6, 3]
    """
    result: List[T] = []
    for i, x in enumerate(array):
        if i:
            result.extend(separator)
        if isinstance(x, list):
            result.extend(x)
        else:
            result.append(x)  # type: ignore
    return result


def pop(array: List[T], index: Optional[int] = None) -> T:
    """
    Remove and return an element from the list at the specified index. If no index
    is specified, removes and returns the last element.

    Args:
        array: The list to pop from.
        index: The index of the element to remove and return. If negative, it counts
               from the end of the list. Defaults to the last element.

    Returns:
        The element removed from the list.

    Raises:
        IndexError: If the list is empty.

    Examples:
        >>> pop([1, 2, 3])
        3
        >>> pop([1, 2, 3], 0)
        1
    """

    if not array:
        raise IndexError("pop from empty list")
    if index is None:
        return array.pop()
    if index < 0:
        index += len(array)
    return array.pop(index)


def pull_at(array: List[T], *indexes: int) -> List[T]:
    """
    Removes elements from `array` corresponding to the specified indexes and returns a list of the
    removed elements. Indexes may be specified as a list of indexes or as individual arguments.

    Args:
        array: List to pull from.
        indexes: Indexes to pull.

    Returns:
        Modified `array`.

    Warning:
        `array` is modified in place.

    Examples:
        >>> pull_at([1, 2, 3, 4], 0, 2)
        [2, 4]
    """
    idxs = list(indexes)
    if len(idxs) == 1 and isinstance(idxs[0], (list, tuple)):
        idxs = list(idxs[0])  # type: ignore
    to_remove = set(i if i >= 0 else i + len(array) for i in idxs)
    return [x for i, x in enumerate(array) if i not in to_remove]


def remove(array: List[T], predicate: Callable[[T], bool]) -> List[T]:
    removed: List[T] = []
    i = 0
    while i < len(array):
        if predicate(array[i]):
            removed.append(array.pop(i))
        else:
            i += 1
    return removed


def slice_(
    array: Union[List[T], str], start: int, end: Optional[int] = None
) -> Union[List[T], str]:
    """
    Return a portion of `array` from index `start` up to, but not including, `end`.

    If `end` is None, return the single element at `start` as a list.

    Args:
        array: The list or string to slice.
        start: The starting index of the slice.
        end: The ending index of the slice (non-inclusive). Defaults to None.

    Returns:
        A list or substring representing the slice.

    Examples:
        >>> slice_([1, 2, 3, 4], 1, 3)
        [2, 3]
        >>> slice_("hello", 1, 4)
        'ell'
    """

    if end is None:
        # return single element at index
        try:
            return [array[start]]  # type: ignore
        except Exception:
            return []
    return array[start:end]  # type: ignore


def ft_reduce(
    func: Callable[[U, T], U], iterable: Iterable[T], initializer: Optional[U] = None
) -> U:
    """
    Applies a rolling computation to sequential pairs of values in an iterable.

    Args:
        func: A binary function to be applied to the items of the iterable.
        iterable: An iterable to be reduced.
        initializer: An initial value for the accumulator.

    Returns:
        The final accumulated value.

    Raises:
        TypeError: If the iterable is empty and no initializer is provided.

    Examples:
        >>> ft_reduce(lambda x, y: x + y, [1, 2, 3, 4, 5])
        15
    """
    it = iter(iterable)
    if initializer is None:
        try:
            acc: U = next(it)  # type: ignore
        except StopIteration:
            raise TypeError("reduce() of empty sequence with no initial value")
    else:
        acc = initializer

    for x in it:
        acc = func(acc, x)
    return acc  # type: ignore


def ft_cmp_to_key(cmp: Callable[[Any, Any], int]):
    """
    Convert a comparison function to a key function that can be used with sorted() etc.

    The comparison function should take two arguments and return a negative integer,
    zero or a positive integer depending on whether the first argument is considered
    smaller than, equal to, or larger than the second argument.

    The returned key function takes one argument and returns an object that can be
    compared with other objects returned by the same key function.

    Examples:
        >>> sorted([4, 2, 9, 6, 5, 1, 8, 3, 7], key=ft_cmp_to_key(lambda x, y: x - y))
        [1, 2, 3, 4, 5, 6, 7, 8, 9]
    """

    class K:
        __slots__ = ("obj",)

        def __init__(self, obj: Any):
            self.obj = obj

        def __lt__(self, other: "K") -> bool: # type: ignore
            return cmp(self.obj, other.obj) < 0 # type: ignore

        def __gt__(self, other: "K") -> bool: # type: ignore
            return cmp(self.obj, other.obj) > 0 # type: ignore

        def __eq__(self, other: "K") -> bool: # type: ignore
            return cmp(self.obj, other.obj) == 0 # type: ignore

        def __le__(self, other: "K") -> bool: # type: ignore
            return cmp(self.obj, other.obj) <= 0 # type: ignore

        def __ge__(self, other: "K") -> bool: # type: ignore
            return cmp(self.obj, other.obj) >= 0 # type: ignore

        def __ne__(self, other: "K") -> bool: # type: ignore
            return cmp(self.obj, other.obj) != 0 # type: ignore

    return K


def sort(
    array: List[Any],
    comparator: Optional[Callable[[Any, Any], int]] = None,
    key: Optional[Callable[[Any], Any]] = None,
    reverse: bool = False,
) -> List[Any]:
    """
    Sorts an array in-place and returns it.

    Args:
        array: The list to sort
        comparator: Optional comparison function that returns -1, 0, or 1
        key: Optional key function to extract comparison value from elements
        reverse: If True, sort in descending order

    Returns:
        The sorted array (same reference as input)

    Raises:
        ValueError: If both comparator and key are provided
        TypeError: If array is not a list or inputs are invalid types

    Security & Stability Notes:
        - Validates input types to prevent injection attacks
        - Uses built-in sorted() for performance and stability
        - Handles edge cases gracefully

    Examples:
        >>> sort([3, 1, 2])
        [1, 2, 3]
    """
    # Security: Validate input types
    if not isinstance(array, list):
        raise TypeError("First argument must be a list")

    if comparator is not None and not callable(comparator):
        raise TypeError("Comparator must be callable")

    if key is not None and not callable(key):
        raise TypeError("Key must be callable")

    # DRY principle: Single validation for mutually exclusive parameters
    if comparator is not None and key is not None:
        raise ValueError("Cannot specify both comparator and key parameters")

    # Performance: Handle empty arrays efficiently
    if not array:
        return array

    # Stability & Performance: Use Python's stable Timsort algorithm
    try:
        if comparator is not None:
            # Convert comparator to key function for performance
            array.sort(key=ft_cmp_to_key(comparator))
        else:
            # Use built-in sort with optional key and reverse
            array.sort(key=key, reverse=reverse)

    except (TypeError, AttributeError) as e:
        # Security: Catch and re-raise with context
        raise TypeError(f"Sort operation failed: {str(e)}")

    return array


def intersection(array: List[T], *arrays: List[T]) -> List[T]:
    """
    Returns an array of values that are present in all arrays.

    Args:
        array: The array to find the intersection of.
        *arrays: Lists to check for intersection with `array`.

    Returns:
        Intersection of provided lists.

    Examples:

        >>> intersection([1, 2, 3], [2, 3, 4])
        [2, 3]
    """
    if not arrays:
        return array.copy()
    result: List[T] = []
    for x in array:
        if x in result:
            continue
        if all(x in arr for arr in arrays):
            result.append(x)
    return result


def intersection_by(array: List[T], *args) -> List[T]:
    # last arg may be iteratee
    """
    Creates an array of unique values that is the intersection of all given arrays, using a provided iteratee to generate the criterion by which uniqueness is computed.

    Args:
        array: The array to inspect.
        *args: The values to intersect.
        iteratee: The iteratee to transform values.

    Returns:
        The intersection of values.

    Examples:
        >>> intersection_by([1, 2, 3], [2, 3, 4], lambda x: x % 2)
        [2]
    """
    iteratee = None
    arrays: List[List[T]] = []
    if args and (callable(args[-1]) or isinstance(args[-1], str) or args[-1] is None):
        iteratee = args[-1]
        arrays = list(args[:-1])  # type: ignore
    else:
        arrays = list(args)  # type: ignore
    if not arrays:
        return array.copy()
    # key function
    if isinstance(iteratee, str):

        def fn(x: T) -> Any:
            if isinstance(x, dict):
                return x.get(iteratee)  # type: ignore  # noqa: E701
            return getattr(x, iteratee, None)  # type: ignore
    elif callable(iteratee):
        fn = iteratee  # type: ignore
    else:
        fn = lambda x: x  # type: ignore  # noqa: E731
    sets = [{fn(v) for v in arr} for arr in arrays]
    seen: set = set()
    result: List[T] = []
    for x in array:
        key_val = fn(x)
        if key_val in seen:
            continue
        if all(key_val in s for s in sets):
            seen.add(key_val)
            result.append(x)
    return result


def unzip_with(
    arrays: List[List[Any]], iteratee: Optional[Callable] = None
) -> List[Any]:
    """
    This method is like unzip except that it accepts an iteratee to specify
    how regrouped values should be combined. The iteratee is invoked with the
    elements of each group.

    Args:
        arrays: List of arrays to process
        iteratee: Optional function to combine the grouped values

    Returns:
        List of regrouped elements, optionally transformed by iteratee

    Security & Performance:
        - Input validation for safety
        - Efficient list comprehension for transposition
        - Handles empty arrays gracefully
        - Supports variable argument functions via unpacking

    Examples:
        >>> unzip_with([[1, 2, 3], [4, 5, 6]], lambda x: sum(x))
        [5, 7, 9]
        >>> unzip_with([])
        []
        >>> unzip_with([[1, 10, 100], [2, 20, 200]])
        [(1, 2), (10, 20), (100, 200)]
        >>> unzip_with([[2, 4, 6], [2, 2, 2]], lambda a, b: a ** b)
        [4, 16, 36]
    """
    # Handle empty input
    if not arrays:
        return []

    # Input validation
    if not isinstance(arrays, (list, tuple)):
        raise TypeError("First argument must be a list or tuple of arrays")

    # Handle empty arrays list
    if len(arrays) == 0:
        return []

    # Validate that all elements are lists/tuples
    for i, arr in enumerate(arrays):
        if not isinstance(arr, (list, tuple)):
            raise TypeError(f"Element at index {i} must be a list or tuple")

    # Handle case where arrays contain empty lists
    if any(len(arr) == 0 for arr in arrays):
        return []

    # Validate iteratee if provided
    if iteratee is not None and not callable(iteratee):
        raise TypeError("Iteratee must be callable")

    # Find the minimum length to avoid index errors
    min_length = min(len(arr) for arr in arrays)

    # If no minimum length, return empty
    if min_length == 0:
        return []

    # Transpose the arrays and optionally apply iteratee
    result = []

    try:
        for i in range(min_length):
            # Get the i-th element from each array
            group = [arr[i] for arr in arrays]

            if iteratee is None:
                # Return as tuple if no iteratee provided
                result.append(tuple(group))
            else:
                # Apply iteratee to the group
                # Use unpacking to support functions that take multiple arguments
                transformed = iteratee(*group)
                result.append(transformed)

    except (TypeError, IndexError) as e:
        raise TypeError(f"Failed to process arrays: {str(e)}")

    return result


def power(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Helper function to calculate a raised to the power of b.
    Used in the test cases for unzip_with.

    Args:
        a: Base number
        b: Exponent

    Returns:
        a raised to the power of b

    Examples:
        >>> power(2, 3)
        8
    """
    return a**b


def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Helper function to calculate a raised to the power of b.
    Used in the test cases for unzip_with.

    Args:
        a: Base number
        b: Exponent

    Returns:
        a raised to the power of b
    """
    return a + b


def zip_with(*args) -> List[Any]:
    """
    Merges together the values of each of the arrays with the
    corresponding values of the other arrays, based on their index.

    Args:
        *args: The arrays to merge

    Returns:
        A list with the merged values

    Examples:
        >>> zip_with([1, 2, 3], [4, 5, 6], [7, 8, 9])
        [(1, 4, 7), (2, 5, 8), (3, 6, 9)]
    """
    if not args:
        return []
    func = args[-1] if callable(args[-1]) else None
    arrays = list(args[:-1]) if func else list(args)
    if func:
        return [func(*group) for group in zip(*arrays)]
    return list(zip(*arrays))


def unshift(array: List[T], *values: T) -> List[T]:
    """
    Adds elements to the beginning of an array.

    Args:
        array: The array to modify
        *values: The values to add to the beginning of the array

    Returns:
        The modified array

    Examples:
        >>> unshift([2, 3], 1)
        [1, 2, 3]
    """
    for v in reversed(values):
        array.insert(0, v)
    return array


def xor(*arrays: List[T]) -> List[T]:
    """
    Creates an array of unique values that is the symmetric difference of the provided arrays.

    Args:
        *arrays: The arrays to process

    Returns:
        A new array with unique values

    Examples:
        >>> xor([1, 2, 3], [2, 3, 4])
        [1, 4]
    """
    if not arrays:
        return []

    def sym(a, b):
        return [x for x in a if x not in b] + [y for y in b if y not in a]

    return ft_reduce(sym, arrays)


def xor_by(*args: Any) -> List[T]:
    """
    Creates an array of unique values that is the symmetric difference of the provided arrays.

    Args:
        *arrays: The arrays to process
        fn: The iteratee applied per element

    Returns:
        A new array with unique values

    Examples:
        >>> xor_by([1, 2, 3], [2, 3, 4], lambda x: x % 2)
        [1, 4]
    """
    arrays = list(args)
    if arrays and callable(arrays[-1]):
        fn = arrays.pop()  # type: ignore
    else:
        raise TypeError("Missing iteratee for xor_by")

    def sym(a, b):
        kb = {fn(x) for x in b}
        ka = {fn(x) for x in a}
        return [x for x in a if fn(x) not in kb] + [y for y in b if fn(y) not in ka]

    return ft_reduce(sym, arrays) if arrays else []


def xor_with(*args: Any) -> List[Any]:
    """
    Creates an array of unique values that is the symmetric difference of the provided arrays
    relative to the comparator function.

    The comparator function is called with two arguments: (value, other), where value is a value
    from an array and other is a value from another array. The comparator should return True if
    the values are equal and False otherwise.

    The order of result values is determined by the order they occur in the input arrays.

    Args:
        *arrays: The arrays to process.
        comparator: A callable comparator function to determine equality of values.

    Returns:
        A new array with unique values.

    Examples:
        >>> xor_with([1, 2, 3], [2, 4], lambda x, y: x == y)
        [1, 3, 4]

    Note: This function is not commutative w.r.t. the comparator function. If you need a
    commutative version, use xor_by instead.
    """
    if len(args) < 2:
        raise ValueError("xor_with requires at least one array and one comparator")
    *arrays, comparator = args

    if not callable(comparator):
        raise TypeError("Last argument must be a callable comparator function")

    # Normalize & validate
    lists: List[List[Any]] = []
    for i, arr in enumerate(arrays):
        if not isinstance(arr, (list, tuple)):
            raise TypeError(f"Argument {i} must be a list or tuple")
        lists.append(list(arr))

    # Trivial: only one array
    if len(lists) == 1:
        return lists[0].copy()

    def _xor2(a: List[Any], b: List[Any]) -> List[Any]:
        out: List[Any] = []
        # keep from a those x for which no y in b satisfies comparator(x,y)
        for x in a:
            try:
                if not any(comparator(x, y) for y in b):
                    out.append(x)
            except Exception as e:
                raise TypeError(f"Comparator function failed: {e}")
        # keep from b those y for which no x in a satisfies comparator(y,x)
        for y in b:
            try:
                if not any(comparator(y, x) for x in a):
                    out.append(y)
            except Exception as e:
                raise TypeError(f"Comparator function failed: {e}")
        return out

    # Fast path for exactly two arrays
    if len(lists) == 2:
        return _xor2(lists[0], lists[1])

    # N-way via reduce
    return ft_reduce(_xor2, lists)


###################################################################################
# Functions Alias
###################################################################################
zip_ = zip
append = push

# still missing
# > def iterdifference
# > def iterduplicates
# > def iterflatten
# > def iterinterleave
# > def iterintersection
# > def iterintersperse
# > def iterunique
