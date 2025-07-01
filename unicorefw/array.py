"""
Array manipulation functions for UniCoreFW.

This module contains functions for working with arrays and list-like structures.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info
"""

import random as random_module
from typing import List, Tuple, Callable, TypeVar, Union, Any, Optional, Set
import builtins  # Import Python's built-ins to avoid recursion

T = TypeVar("T")
U = TypeVar("U")
K = TypeVar("K")


def map(array: List[T], func: Callable[[T], U]) -> List[U]:
    """
    Apply a function to each element of an array and return a new array.

    Args:
        array: The array to map
        func: The function to apply to each element

    Returns:
        A new array with the results of applying func to each element
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
    """
    result = initial
    for x in array:
        if result is None:
            result = x
        else:
            result = func(result, x)
    return result


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
    """
    return list(set(array))


def first(*args, **kwargs) -> Union[T, List[T], None]:
    """
    Return the first element of an array or the first `n` elements if specified.

    Args:
        *args: The array or array elements, and possibly `n`
        **kwargs: Optional keyword argument 'n'

    Returns:
        The first element or first `n` elements of the array
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

    return array[:n]


def last(*args, **kwargs) -> Union[T, List[T], None]:
    """
    Return the last element of an array or the last `n` elements if specified.

    Args:
        *args: The array or array elements
        **kwargs: Optional keyword argument 'n'

    Returns:
        The last element or last `n` elements of the array
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

    return array[-n:]


def compact(array: List[Any]) -> List[Any]:
    """
    Remove falsey values from an array.

    Args:
        array: The array to compact

    Returns:
        A new array with falsey values removed
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
    """
    return list(builtins.zip(*arrays))


def unzip(array_of_tuples: List[Tuple]) -> List[List]:
    """
    Reverse the zip operation by separating tuples into arrays.

    Args:
        array_of_tuples: An array of tuples

    Returns:
        A list of arrays
    """
    return list(builtins.map(list, builtins.zip(*array_of_tuples)))


def partition(array: List[T], predicate: Callable[[T], bool]) -> List[List[T]]:
    """
    Partition an array into two lists based on a predicate.

    Args:
        array: The array to partition
        predicate: A function that returns True or False

    Returns:
        A list of two lists [truthy, falsy]
    """
    truthy = [item for item in array if predicate(item)]
    falsy = [item for item in array if not predicate(item)]
    return [truthy, falsy]


def last_index_of(array: List[T], value: T) -> int:
    """
    Return the last index of a specified value in an array.

    Args:
        array: The array to search
        value: The value to find

    Returns:
        The last index of the value, or -1 if not found
    """
    for i in builtins.range(len(array) - 1, -1, -1):
        if array[i] == value:
            return i
    return -1


def chunk(array: List[T], size: int) -> List[List[T]]:
    """
    Split an array into chunks of specified size.

    Args:
        array: The array to chunk
        size: The chunk size

    Returns:
        A list of chunks
    """
    return [array[i : i + size] for i in builtins.range(0, len(array), size)]


def initial(array: List[T], n: int = 1) -> List[T]:
    """
    Return all elements except the last n elements.

    Args:
        array: The array
        n: Number of elements to exclude from the end

    Returns:
        A new array without the last n elements
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
    """
    depth+=1
    
    if array is None:
        return []

    if depth is True:
        depth = 1
    elif isinstance(depth, (int, float)) and depth < 0:
        return array

    result = []
    stack = [(array, depth)]

    while stack:
        current, current_depth = stack.pop()
        if isinstance(current, list) and current_depth != 0:
            # We reverse for correct left-to-right processing via LIFO
            for item in reversed(current):
                stack.append((item, current_depth - 1 if current_depth != float("inf") else current_depth))
        else:
            result.append(current)

    return result



def reject(array: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """
    Return items that do not match the predicate.

    Args:
        array: The array to filter
        predicate: A function that returns True for items to reject

    Returns:
        A new array with rejected items removed
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
    """
    other_elements = set().union(*others)
    return [x for x in array if x not in other_elements]


def union(*arrays) -> List:
    """
    Combine arrays and remove duplicates.

    Args:
        *arrays: Arrays to combine

    Returns:
        A new array with unique values from all input arrays
    """
    return list(set().union(*arrays))


def intersection(*arrays) -> List:
    """
    Return an array of values common to all arrays.

    Args:
        *arrays: Arrays to intersect

    Returns:
        A new array with values present in all input arrays
    """
    if not arrays:
        return []

    common_elements = set(arrays[0])
    for arr in arrays[1:]:
        common_elements.intersection_update(arr)

    return list(common_elements)


def sort_by(array: List[T], key_func: Callable[[T], Any]) -> List[T]:
    """
    Sort an array by a function or key.

    Args:
        array: The array to sort
        key_func: A function that returns a comparable value

    Returns:
        A new sorted array
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
    """
    if not array:
        return None
    if key_func:
        return builtins.max(array, key=key_func)
    return builtins.max(array)


def min_value(
    array: List[T], key_func: Optional[Callable[[T], Any]] = None
) -> Optional[T]:
    """
    Return the minimum value in the array, based on an optional key function.
    Returns None if the array is empty.
    """
    if not array:
        return None
    if key_func:
        return builtins.min(array, key=key_func)
    return builtins.min(array)


def find_median_sorted_arrays(nums1: List[float], nums2: List[float]) -> float:
    """
    Find the median of two sorted arrays using binary search.

    Args:
        nums1: First sorted array
        nums2: Second sorted array

    Returns:
        The median value
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
