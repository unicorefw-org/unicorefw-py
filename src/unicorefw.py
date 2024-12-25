########################################################################
# unicorefw.py - Universal Core Utility Library                        #
# Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info          #
#                                                                      #
# This file is part of UniCoreFW.                                      #
# UniCore is free software: you can redistribute it and/or modify      #
# it under the terms of the [BSD-3-Clause] as published by             #
# the Free Software Foundation.                                        #
# You should have received a copy of the [BSD-3-Clause] license        #
# along with UniCoreFW. If not, see https://www.gnu.org/licenses/.     #
########################################################################

import re
import random
import threading
import time
import types

class UniCoreFW(object):
    _id_counter = 0  # Initialize the counter

    def __init__(self, collection):
        self._version = "1.0.0"
        self._name = "UniCoreFW"
        self._author = "Kenny Ngo"
        self._description = "Universal Core Utility Library"
        self.wrapper = UniCoreFWWrapper(collection)

    def __getattr__(self, item):
        # Delegate attribute access to the wrapped instance
        if hasattr(self.wrapper, item):
            return getattr(self.wrapper, item)
        elif hasattr(UniCoreFW, item):
            return getattr(UniCoreFW, item)
        raise AttributeError(f"'UniCoreFW' object has no attribute '{item}'")

    def __call__(self, collection):
        # Return a new UniCoreFWWrapper instance when called
        return UniCoreFWWrapper(collection)

    #############################################################################
    # Unicore Utility Functions                                                 #
    #############################################################################
    @staticmethod
    def find_median_sorted_arrays(nums1, nums2):
        """
        Finds the median of two sorted arrays using binary search.

        This function uses binary search to find the median of two sorted arrays, nums1 and nums2.
        It ensures that nums1 is the smaller array for efficiency.

        The time complexity for this function is O(log(min(m, n))), where m and n are the lengths
        of nums1 and nums2, respectively.

        The space complexity for this function is O(1), since it only uses a constant amount of space.

        Parameters:
        nums1 (list): The first sorted array.
        nums2 (list): The second sorted array.

        Returns:
        float: The median of the two sorted arrays.
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

    @staticmethod
    def decompress(comp):
        """
        Decompresses a given string, which is compressed using run-length encoding.

        The compressed string is given as a parameter, and the function will return the decompressed string.

        For example, if the input string is "3(a)2(b)3(c)", the output will be "aaabbccc".

        :param comp: The compressed string to be decompressed.
        :return: The decompressed string.
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

    @staticmethod
    def compress(word):
        """
        Compresses a string using a simple run-length encoding.

        This method compresses the input string by replacing sequences of repeated characters
        with a single instance of the character followed by a number indicating the count
        of repetitions. The count is capped at 9 to avoid ambiguity in decoding.

        Parameters:
        word (str): The input string to be compressed.

        Returns:
        str: A compressed version of the input string using run-length encoding.
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

    # -------- Array Functions -------- #
    @staticmethod
    def map(array, func):
        """Applies func to each element of the array and returns a new array."""
        return [func(x) for x in array]

    @staticmethod
    def reduce(array, func, initial=None):
        """Reduces the array to a single value using the func and an optional initial value."""
        result = initial
        for x in array:
            if result is None:
                result = x
            else:
                result = func(result, x)
        return result

    @staticmethod
    def find(array, func):
        """
        Finds the first element in the array that matches the predicate func.

        Security Considerations:
            - Validates inputs to prevent type-related errors.
            - Catches and handles exceptions raised by func(x).
            - Avoids modifying the input array.
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

    @staticmethod
    def uniq(array):
        """Removes duplicates from the array."""
        return list(set(array))

    @staticmethod
    def first(*args, **kwargs):
        """
        Returns the first element of an array or the first `n` elements if specified.

        Parameters:
            *args: The array or array elements, and possibly `n`.
            **kwargs: Optional keyword argument 'n'.

        Returns:
            The first element or first `n` elements of the array.
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

    @staticmethod
    def last(*args, **kwargs):
        """
        Returns the last element of an array or the last `n` elements if specified.

        Parameters:
            *args: The array or array elements.
            **kwargs: Optional keyword argument 'n'.

        Returns:
            The last element or last `n` elements of the array.
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

    @staticmethod
    def compact(array):
        """Removes falsey values from an array."""
        return [x for x in array if x]

    @staticmethod
    def without(array, *values):
        """Returns an array excluding all provided values."""
        return [x for x in array if x not in values]

    @staticmethod
    def pluck(array, key):
        """Extracts a list of property values from an array of objects."""
        return [
            obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)
            for obj in array
        ]

    @staticmethod
    def shuffle(array):
        """Randomly shuffles the values in an array."""
        # Use the Fisher-Yates shuffle algorithm, which is secure and efficient
        array_copy = list(array)
        for i in range(len(array_copy) - 1, 0, -1):
            j = random.randint(0, i)
            array_copy[i], array_copy[j] = array_copy[j], array_copy[i]
        return array_copy

    @staticmethod
    def zip(*arrays):
        """Combines multiple arrays into an array of tuples."""
        return list(zip(*arrays))

    @staticmethod
    def unzip(array_of_tuples):
        """Reverses the zip operation by separating tuples into arrays."""
        return list(map(list, zip(*array_of_tuples)))

    @staticmethod
    def partition(array, predicate):
        """
        Partitions an array into two lists based on a predicate.
        """
        truthy = [item for item in array if predicate(item)]
        falsy = [item for item in array if not predicate(item)]
        return [truthy, falsy]

    @staticmethod
    def last_index_of(array, value):
        """Returns the last index of a specified value in an array."""
        for i in range(len(array) - 1, -1, -1):
            if array[i] == value:
                return i
        return -1

    # -------- Object Functions -------- #
    @staticmethod
    def keys(obj):
        """Returns the keys of a dictionary."""
        return list(obj.keys())

    @staticmethod
    def values(obj):
        """Returns the values of a dictionary."""
        return list(obj.values())

    @staticmethod
    def extend(obj, *sources):
        """Extends obj by copying properties from sources."""
        for source in sources:
            obj.update(source)
        return obj

    @staticmethod
    def clone(obj):
        """Creates a shallow copy of an object (dictionary or list)."""
        if isinstance(obj, dict):
            return obj.copy()
        elif isinstance(obj, list):
            return list(obj)
        else:
            return obj

    @staticmethod
    def has(obj, key):
        """Checks if obj has a given property key."""
        return key in obj

    @staticmethod
    def invert(obj):
        """Inverts an object's keys and values."""
        return {v: k for k, v in obj.items()}

    def defaults(obj, *defaults):
        """
        Assigns default properties to obj if they are missing.

        Parameters:
            obj (dict): The original dictionary to update.
            *defaults (dict): One or more dictionaries containing default values.

        Returns:
            dict: A new dictionary with defaults applied.

        Security Considerations:
            - Validates that 'obj' and 'defaults' are dictionaries.
            - Checks that keys in 'defaults' are strings.
            - Does not modify 'obj' in-place to prevent unintended side effects.
        """
        if not isinstance(obj, dict):
            raise TypeError("The 'obj' parameter must be a dictionary.")

        # Create a copy to avoid modifying the original object
        result = obj.copy()

        for default in defaults:
            if not isinstance(default, dict):
                raise TypeError("Each default must be a dictionary.")
            for key, value in default.items():
                if key not in obj:
                    obj[key] = value
                if not isinstance(key, str):
                    raise ValueError("Keys in defaults must be strings.")
                # Only set the default if the key is not already in 'result'
                if key not in result:
                    result[key] = value
        return result

    @staticmethod
    def create(proto):
        """
        Creates an object that inherits from the given prototype (dictionary).
        """
        if not isinstance(proto, dict):
            raise TypeError("Prototype must be a dictionary")

        class Obj(dict):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.update(proto)

        return Obj()

    @staticmethod
    def pairs(obj):
        """Converts an object into an array of [key, value] pairs."""
        return list(obj.items())

    @staticmethod
    def result(obj, property_name, *args):
        """If the property is a function, invoke it with args; otherwise, return the property value."""
        value = obj.get(property_name)

        if callable(value):
            # Directly call the function with args if it's callable
            return value(*args)

        return value

    @staticmethod
    def size(obj):
        """Returns the number of values in obj (works for dicts, lists, etc.)."""
        if hasattr(obj, "__len__"):
            return len(obj)
        return sum(1 for _ in obj)

    @staticmethod
    def to_array(obj):
        """Converts obj into an array (list in Python)."""
        if isinstance(obj, list):
            return obj
        elif isinstance(obj, (dict, set)):
            return list(obj.values()) if isinstance(obj, dict) else list(obj)
        elif hasattr(obj, "__iter__"):
            return list(obj)
        return [obj]

    @staticmethod
    def where(obj_list, properties):
        """Returns an array of all objects in obj_list that match the key-value pairs in properties."""
        return [
            obj
            for obj in obj_list
            if all(obj.get(k) == v for k, v in properties.items())
        ]

    @staticmethod
    def object(keys, values):
        """
        Creates an object (dictionary) from the given keys and values.
        """
        if len(keys) != len(values):
            raise ValueError("Keys and values must have the same length")
        return {keys[i]: values[i] for i in range(len(keys))}

    # -------- Type Checking -------- #
    @staticmethod
    def is_string(obj):
        """Checks if obj is a string."""
        return isinstance(obj, str)

    @staticmethod
    def is_number(obj):
        """Checks if obj is a number (int or float)."""
        return isinstance(obj, (int, float))

    @staticmethod
    def is_array(obj):
        """Checks if obj is a list."""
        return isinstance(obj, list)

    @staticmethod
    def is_object(obj):
        """Checks if obj is a dictionary."""
        return isinstance(obj, dict)

    @staticmethod
    def is_function(obj):
        """Checks if obj is callable (function)."""
        return callable(obj)

    @staticmethod
    def is_boolean(obj):
        """Checks if obj is a boolean."""
        return isinstance(obj, bool)

    @staticmethod
    def is_date(obj):
        """Checks if obj is a date object."""
        from datetime import date

        return isinstance(obj, date)

    @staticmethod
    def is_reg_exp(obj):
        """Checks if obj is a regular expression."""
        return isinstance(obj, re.Pattern)

    @staticmethod
    def is_error(obj):
        """Checks if obj is an error instance."""
        return isinstance(obj, Exception)

    @staticmethod
    def is_null(obj):
        """Checks if obj is None."""
        return obj is None

    @staticmethod
    def is_undefined(obj):
        """Checks if obj is undefined (None in Python)."""
        return obj is None

    @staticmethod
    def is_finite(obj):
        """Checks if obj is a finite number."""
        from math import isfinite

        return isinstance(obj, (int, float)) and isfinite(obj)

    @staticmethod
    def is_nan(obj):
        """Checks if obj is NaN."""
        from math import isnan

        return isinstance(obj, float) and isnan(obj)

    @staticmethod
    def is_map(obj):
        """Checks if obj is a map."""
        return isinstance(obj, dict)

    @staticmethod
    def is_set(obj):
        """Checks if obj is a set."""
        return isinstance(obj, set)

    @staticmethod
    def is_arguments(obj):
        """Checks if obj is an arguments object (useful in JavaScript, not directly applicable in Python)."""
        # Since Python doesn't have a direct "arguments" object, we check if obj is a tuple,
        # which is a common way to represent function arguments in Python.
        return isinstance(obj, tuple)

    @staticmethod
    def is_array_buffer(obj):
        """Checks if obj is an ArrayBuffer. In Python, we approximate with bytearray."""
        import array

        return isinstance(obj, array.array)

    @staticmethod
    def is_data_view(obj):
        """Checks if obj is a DataView. In Python, memoryview is similar to a DataView in JavaScript."""
        return isinstance(obj, memoryview)

    @staticmethod
    def is_typed_array(obj):
        """Checks if obj is a typed array. In Python, we approximate with array.array."""
        from array import array

        return isinstance(obj, array)

    @staticmethod
    def is_weak_map(obj):
        """Checks if obj is a WeakMap. Python equivalent is weakref.WeakKeyDictionary."""
        from weakref import WeakKeyDictionary

        return isinstance(obj, WeakKeyDictionary)

    @staticmethod
    def is_weak_set(obj):
        """Checks if obj is a WeakSet. Python equivalent is weakref.WeakSet."""
        from weakref import WeakSet

        return isinstance(obj, WeakSet)

    @staticmethod
    def is_element(obj):
        """Checks if obj is a DOM element. This is browser-specific, so in Python, we can check for an ElementTree element."""
        try:
            from xml.etree.ElementTree import Element

            return isinstance(obj, Element)
        except ImportError:
            return False

    @staticmethod
    def is_empty(obj):
        """Checks if an object is empty."""
        if obj is None:
            return True
        if hasattr(obj, "__len__"):
            return len(obj) == 0
        if hasattr(obj, "__iter__"):
            return not any(True for _ in obj)
        return False

    @staticmethod
    def is_match(obj, attrs):
        """Checks if obj has key-value pairs that match attrs."""
        return all(obj.get(k) == v for k, v in attrs.items())

    @staticmethod
    def is_symbol(obj):
        """
        Checks if an object is a type that could be considered a 'symbol' in Python.
        This includes module types, function types, and unique identifiers.
        """
        return isinstance(
            obj, (types.ModuleType, types.BuiltinFunctionType, types.FunctionType, type)
        )

    # -------- Utility Functions -------- #
    @staticmethod
    def identity(value):
        """Returns the given value unchanged."""
        return value

    @staticmethod
    def times(n, func):
        """
        Calls the given function `n` times, passing the iteration index to `func`, and returns a list of the results.
        """
        return [func(i) for i in range(n)]

    @staticmethod
    def unique_id(prefix=""):
        """Generates a unique identifier with an optional prefix."""
        UniCoreFW._id_counter += 1
        return f"{prefix}{UniCoreFW._id_counter}"

    @staticmethod
    def escape(string):
        """Escapes HTML characters in a string."""
        escape_map = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "`": "&#x60;",
        }
        return "".join(escape_map.get(c, c) for c in string)

    @staticmethod
    def unescape(string):
        """Unescapes HTML characters in a string."""
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

    @staticmethod
    def now():
        """Returns the current timestamp."""
        return int(time.time() * 1000)

    @staticmethod
    def memoize(func):
        """Caches the results of function calls."""
        cache = {}

        def memoized_func(*args):
            if args not in cache:
                cache[args] = func(*args)
            return cache[args]

        return memoized_func

    # -------- Function Utilities -------- #
    @staticmethod
    def partial(func, *partial_args):
        """Partially applies arguments to a function."""

        def partially_applied(*extra_args):
            return func(*(partial_args + extra_args))

        return partially_applied

    @staticmethod
    def throttle(func, wait):
        """Throttles a function to be called at most once every wait milliseconds."""
        import time

        last_called = [0]

        def throttled_func(*args, **kwargs):
            now = time.time()
            if now - last_called[0] > wait / 1000:
                last_called[0] = now
                return func(*args, **kwargs)

        return throttled_func

    @staticmethod
    def debounce(func, wait, *, use_main_thread=False):
        """
        Debounces a function to only be called after wait milliseconds.

        Parameters:
            func (callable): The function to debounce.
            wait (int): The delay in milliseconds.
            use_main_thread (bool): If True, ensures `func` is called in the main thread.

        Returns:
            callable: The debounced function.
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

    @staticmethod
    def once(func):
        """Ensures a function is only called once, returning None on subsequent calls."""
        result = [None]
        has_been_called = [False]

        def once_func(*args, **kwargs):
            if not has_been_called[0]:
                result[0] = func(*args, **kwargs)
                has_been_called[0] = True
            else:
                result[0] = None  # Return None after the first call
            return result[0]

        return once_func

    @staticmethod
    def after(times, func):
        """Returns a function that will only run after it's been called a specified number of times."""
        calls = [0]

        def after_func(*args, **kwargs):
            calls[0] += 1
            if calls[0] >= times:
                return func(*args, **kwargs)

        return after_func

    @staticmethod
    def compose(*funcs):
        """Composes multiple functions to execute in sequence."""

        def composed(value):
            for func in reversed(funcs):
                value = func(value)
            return value

        return composed

    @staticmethod
    def invoke(array, func_name, *args):
        """Calls a method on each item in an array."""
        return [
            getattr(item, func_name)(*args) if hasattr(item, func_name) else None
            for item in array
        ]

    @staticmethod
    def matches(attrs):
        """Returns a function that checks if an object matches key-value pairs."""

        def match(obj):
            return all(obj.get(k) == v for k, v in attrs.items())

        return match

    def all_keys(obj):
        """
        Returns all the keys of a dictionary, including inherited ones.
        """
        if isinstance(obj, dict):
            return list(obj.keys())
        else:
            raise TypeError("The input must be a dictionary.")

    @staticmethod
    def bind(func, context, *args):
        """Binds a function to a context with optional pre-filled arguments."""

        def bound_func(*extra_args):
            return func(
                *(args + extra_args)
            )  # Only pass args and extra_args without context

        return bound_func

    # -------- Advanced Array Functions -------- #
    @staticmethod
    def sort_by(array, key_func):
        """Sorts an array by a function or key."""
        return sorted(array, key=key_func)

    @staticmethod
    def group_by(array, key_func):
        """Groups array elements by the result of a function."""
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

    # -------- Deep Comparison -------- #
    @staticmethod
    def is_equal(obj1, obj2):
        """Performs a deep comparison between two objects for equality."""
        if type(obj1) != type(obj2):
            return False
        if isinstance(obj1, dict):
            if len(obj1) != len(obj2):
                return False
            return all(
                k in obj2 and UniCoreFW.is_equal(v, obj2[k]) for k, v in obj1.items()
            )
        elif isinstance(obj1, list):
            if len(obj1) != len(obj2):
                return False
            return all(UniCoreFW.is_equal(x, y) for x, y in zip(obj1, obj2))
        return obj1 == obj2

    # -------- Helpers and Miscellaneous -------- #
    @staticmethod
    def noop():
        """A function that does nothing (no operation)."""
        pass

    @staticmethod
    def constant(value):
        """Returns a function that always returns the specified value."""
        return lambda: value

    @staticmethod
    def random(min_val, max_val):
        """Returns a random integer between min_val and max_val, inclusive."""
        from random import randint

        return randint(min_val, max_val)

    @staticmethod
    def some(array, func):
        """Checks if at least one element in the array matches the predicate."""
        return any(func(x) for x in array)

    @staticmethod
    def every(array, func):
        """Checks if every element in the array matches the predicate."""
        return all(func(x) for x in array)

    @staticmethod
    def wrap(func, wrapper):
        """Wraps a function inside a wrapper function."""

        def wrapped(*args, **kwargs):
            return wrapper(func, *args, **kwargs)

        return wrapped

    @staticmethod
    def iteratee(value):
        """Returns a function based on the type of value (identity if callable, otherwise a matcher)."""
        if callable(value):
            return value
        elif isinstance(value, dict):
            return lambda obj: all(obj.get(k) == v for k, v in value.items())
        else:
            return lambda obj: obj == value

    @staticmethod
    def max(array, key_func=None):
        """Returns the maximum value in the array, based on an optional key function."""
        if not array:
            return None
        if key_func:
            return max(array, key=key_func)
        return max(array)

    @staticmethod
    def min(array, key_func=None):
        """Returns the minimum value in the array, based on an optional key function."""
        if not array:
            return None
        if key_func:
            return min(array, key=key_func)
        return min(array)

    @staticmethod
    def mixin(obj):
        """Adds properties of obj as functions on UniCoreFW itself."""
        for key, func in obj.items():
            if callable(func):
                setattr(UniCoreFW, key, func)

    @staticmethod
    def chain(obj):
        """Enables chaining by wrapping the object in a chainable class."""

        class Chained:
            def __init__(self, obj):
                self._wrapped = obj

            def value(self):
                return self._wrapped

            def __getattr__(self, attr):
                func = getattr(UniCoreFW, attr)
                if callable(func):

                    def chainable(*args, **kwargs):
                        result = func(self._wrapped, *args, **kwargs)
                        if result is None:
                            return self
                        return Chained(result)

                    return chainable
                raise AttributeError(f"{attr} is not a valid attribute")

        return Chained(obj)

    @staticmethod
    def tap(value, func):
        """Invokes func with the value and then returns value."""
        func(value)
        return value

    # -------- Utility and Array Functions -------- #
    @staticmethod
    def chunk(array, size):
        """Splits an array into chunks of specified size."""
        return [array[i : i + size] for i in range(0, len(array), size)]

    @staticmethod
    def initial(array, n=1):
        """Returns all elements except the last n elements."""
        return array[:-n] if n < len(array) else []

    @staticmethod
    def rest(array, n=1):
        """Returns all elements except the first n elements."""
        return array[n:]

    @staticmethod
    def contains(array, value):
        """Checks if a value is present in the array."""
        return value in array

    def flatten(*args, depth=None):
        """
        Flattens nested lists up to the specified depth.

        Parameters:
            *args: The array or array elements. Can be multiple positional arguments.
            depth (int, optional): The depth level specifying how deep a nested list structure should be flattened.
                                If None, it flattens infinitely deep.

        Returns:
            list: A flattened list containing the elements up to the specified depth.
        """
        # Determine if the last positional argument is 'n' (depth) when depth is not specified
        if depth is None and len(args) >= 1 and isinstance(args[-1], int):
            n = args[-1]
            args = args[:-1]
        else:
            n = depth

        # Validate 'n' (depth)
        if n is not None:
            if isinstance(n, bool):
                n = int(n)
            elif not isinstance(n, int):
                raise ValueError("Depth must be a non-negative integer or None.")
            if n < 0:
                raise ValueError("Depth must be a non-negative integer or None.")

        # Determine the array to flatten
        if len(args) == 1 and isinstance(args[0], list):
            array = args[0]
        else:
            array = list(args)

        # Handle edge cases for None or empty lists
        if array is None or not array:
            return [] if n is not None else None

        # Set maximum depth
        max_depth = float("inf") if n is None else n

        result = []

        def _flatten(current, current_depth):
            for item in current:
                if isinstance(item, list) and current_depth > 0:
                    _flatten(item, current_depth - 1)
                else:
                    result.append(item)

        _flatten(array, max_depth)
        return result

    @staticmethod
    def reject(array, predicate):
        """The opposite of filter; returns items that do not match the predicate."""
        return [x for x in array if not predicate(x)]

    @staticmethod
    def filter(array, func):
        """Filters elements in array based on func predicate."""
        return [x for x in array if func(x)]

    @staticmethod
    def sample(array, n=1):
        """Returns a random sample from an array."""
        from random import sample

        return sample(array, n if n < len(array) else len(array))

    @staticmethod
    def index_by(array, key_func):
        """
        Indexes the array by a specific key or a function.
        If key_func is a string, it will use that string as a key to index the objects.
        """
        if isinstance(key_func, str):
            return {item[key_func]: item for item in array if key_func in item}
        else:
            return {key_func(item): item for item in array}

    @staticmethod
    def count_by(array, key_func):
        """Counts instances in an array based on a function's result."""
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

    # -------- Additional Utility Functions -------- #
    @staticmethod
    def negate(func):
        """Returns the negation of a predicate function."""
        return lambda *args, **kwargs: not func(*args, **kwargs)

    @staticmethod
    def property(prop_name):
        """Returns a function that retrieves a property value by name."""
        return (
            lambda obj: obj.get(prop_name)
            if isinstance(obj, dict)
            else getattr(obj, prop_name, None)
        )

    @staticmethod
    def property_of(obj):
        """Returns a function that retrieves a property value from a given object."""
        return (
            lambda prop_name: obj.get(prop_name)
            if isinstance(obj, dict)
            else getattr(obj, prop_name, None)
        )

    @staticmethod
    def matcher(attrs):
        """Returns a function that checks if an object has matching key-value pairs."""

        def match(obj):
            return all(obj.get(k) == v for k, v in attrs.items())

        return match

    @staticmethod
    def difference(array, *others):
        """Returns values from the first array not present in others."""
        other_elements = set().union(*others)
        return [x for x in array if x not in other_elements]

    @staticmethod
    def range(start, stop=None, step=1):
        """Generates an array of numbers in a range."""
        if stop is None:
            start, stop = 0, start
        return list(range(start, stop, step))

    @staticmethod
    def union(*arrays):
        """Combines arrays and removes duplicates."""
        return list(set().union(*arrays))

    @staticmethod
    def intersection(*arrays):
        """Returns an array of values common to all arrays."""
        common_elements = set(arrays[0])
        for arr in arrays[1:]:
            common_elements.intersection_update(arr)
        return list(common_elements)

    @staticmethod
    def before(n, func):
        """Returns a function that can be called up to n times."""
        result = [None]
        calls = [0]

        def limited_func(*args, **kwargs):
            if calls[0] < n:
                result[0] = func(*args, **kwargs)
                calls[0] += 1
            return result[0]

        return limited_func

    @staticmethod
    def bind_all(obj, *methodNames):
        """Binds specified methods of obj to obj itself."""
        for method_name in methodNames:
            if hasattr(obj, method_name):
                bound_method = getattr(obj, method_name).__get__(obj)
                setattr(obj, method_name, bound_method)

    @staticmethod
    def defer(func, *args, **kwargs):
        """Defers invoking the function until the current call stack has cleared."""
        threading.Timer(0, func, args=args, kwargs=kwargs).start()

    @staticmethod
    def delay(func, wait, *args, **kwargs):
        """Invokes func after a specified number of milliseconds."""
        threading.Timer(wait / 1000, func, args=args, kwargs=kwargs).start()

    @staticmethod
    def functions(obj):
        """
        Returns the names of all explicitly defined functions in an object (dictionary).

        Parameters:
            obj (dict): The dictionary to check for functions.

        Returns:
            list: A list of function names defined in the object.
        """
        if not isinstance(obj, dict):
            raise TypeError("Input must be a dictionary.")

        return [
            key
            for key, value in obj.items()
            if callable(value) and not key.startswith("__")
        ]

    @staticmethod
    def map_object(obj, func):
        """Applies func to each value in obj, returning a new object with the transformed values."""
        return {k: func(v) for k, v in obj.items()}

    @staticmethod
    def template(template, context):
        token_pattern = r"(<%=?[^%]*?%>)"

        def tokenize(template):
            tokens = re.split(token_pattern, template)
            return tokens

        def evaluate_expression(expr, context):
            # Allow simple variable access and method calls
            pattern = r"^([a-zA-Z_][a-zA-Z0-9_]*)(\.[a-zA-Z_][a-zA-Z0-9_]*(\(\))?)*$"
            if not re.match(pattern, expr):
                raise ValueError(f"Invalid expression: '{expr}'")

            parts = expr.split(".")
            value = context.get(parts[0], None)
            if value is None:
                raise NameError(f"Name '{parts[0]}' is not defined.")

            for part in parts[1:]:
                if part.endswith("()"):
                    method_name = part[:-2]
                    value = call_safe_method(value, method_name)
                else:
                    if hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        raise AttributeError(f"Attribute '{part}' not found.")
            return value

        def evaluate_condition(condition, context):
            # Allow simple variable truthiness checks
            pattern = r"^([a-zA-Z_][a-zA-Z0-9_]*)$"
            if not re.match(pattern, condition):
                raise ValueError(f"Invalid condition: '{condition}'")

            value = context.get(condition, None)
            return bool(value)

        def call_safe_method(obj, method_name):
            # Only allow safe methods on strings
            safe_methods = {"upper", "lower", "title", "capitalize"}
            if isinstance(obj, str) and method_name in safe_methods:
                method = getattr(obj, method_name)
                return method()
            else:
                raise ValueError(
                    f"Method '{method_name}' is not allowed on object of type '{type(obj).__name__}'."
                )

        tokens = tokenize(template)
        output = ""
        skip_stack = []
        idx = 0

        while idx < len(tokens):
            token = tokens[idx]
            # token = token.strip('\n')
            if token.startswith("<%=") and token.endswith("%>"):
                if not any(skip_stack):
                    expr = token[3:-2].strip()
                    value = evaluate_expression(expr, context)
                    output += str(value)
            elif token.startswith("<%") and token.endswith("%>"):
                tag_content = token[2:-2].strip()
                if tag_content.startswith("if "):
                    condition = tag_content[3:].rstrip(":").strip()
                    result = evaluate_condition(condition, context)
                    skip_stack.append(not result)
                elif tag_content == "endif":
                    if skip_stack:
                        skip_stack.pop()
                    else:
                        raise ValueError("Unmatched 'endif' found.")
                else:
                    raise ValueError(f"Unknown tag '{tag_content}'.")
            else:
                if not any(skip_stack):
                    output += token
            idx += 1

        if skip_stack:
            raise ValueError("Unclosed 'if' statement detected.")
        return output

    @staticmethod
    def deep_copy(obj):
        """Creates a deep copy of the given object without using imports."""
        if isinstance(obj, dict):
            return {k: UniCoreFW.deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [UniCoreFW.deep_copy(elem) for elem in obj]
        elif isinstance(obj, tuple):
            return tuple(UniCoreFW.deep_copy(elem) for elem in obj)
        elif isinstance(obj, str):
            # Strings are immutable, return as is
            return obj
        else:
            # For immutable objects like int, float, return as is
            return obj


    # Optional factory method for creating an instance
    @classmethod
    def _(cls, collection):
        return cls(collection)


################################################################################################################
## UniCoreFWWrapper
################################################################################################################
class UniCoreFWWrapper(object):
    def __init__(self, collection):
        """
        Initializes a new instance of the UniCoreFWWrapper class with the provided collection.

        Parameters:
            collection (iterable): The collection of items to be wrapped and manipulated
            using the UniCoreFW functions.
        """

        self.collection = collection

    def _apply_unicore_function(self, function_name, *args, **kwargs):
        func = getattr(UniCoreFW, function_name, None)
        if callable(func):
            result = func(self.collection, *args, **kwargs)
        elif hasattr(self.collection, function_name) and callable(
            getattr(self.collection, function_name)
        ):
            method = getattr(self.collection, function_name)
            result = method(*args, **kwargs)
        else:
            raise AttributeError(
                f"'unicore' and Python do not have a callable function named '{function_name}'"
            )

        if isinstance(result, (list, tuple, set)):
            return UniCoreFWWrapper(result)
        return result

    def _bind_unicore_functions(self, obj):
        # Attach functions from 'UniCoreFW' directly to '_'
        for func_name in dir(UniCoreFW):
            if callable(getattr(UniCoreFW, func_name)) and not func_name.startswith("_"):
                setattr(obj, func_name, getattr(UniCoreFW, func_name))

        return obj

    def value(self):
        return self.collection

    def chain(self):
        """Starts a chain of operations."""
        return self

    # Generate methods for all functions in unicore
    def map(self, func):
        """Applies the provided function to each element of the collection and returns a new collection."""
        return self._apply_unicore_function("map", func)

    def filter(self, predicate):
        """
        Filters the elements of the collection based on the provided predicate function.

        Parameters:
            predicate (function): A function that takes an element of the collection as its argument and
                returns a boolean value indicating whether the element should be included in the new
                collection.

        Returns:
            UniCoreFWWrapper: A new UniCoreFWWrapper instance with the filtered elements.
        """
        return self._apply_unicore_function("filter", predicate)

    def reduce(self, func, initial=None):
        """
        Reduces the collection to a single value using the provided function.

        Parameters:
            func (function): A function that takes two arguments: the current accumulated value and the current element of the collection.
            initial: An optional initial value to be used as the first argument to the function.

        Returns:
            object: The result of the reduction.
        """
        return (
            self._apply_unicore_function("reduce", func, initial)
            if initial is not None
            else self._apply_unicore_function("reduce", func)
        )

    def sort_by(self, key_func):
        return self._apply_unicore_function("sort_by", key_func)

    def group_by(self, key_func):
        return self._apply_unicore_function("group_by", key_func)

    def index_by(self, key_func):
        return self._apply_unicore_function("index_by", key_func)

    def count_by(self, key_func):
        return self._apply_unicore_function("count_by", key_func)

    def find(self, predicate):
        return self._apply_unicore_function("find", predicate)

    def uniq(self):
        return self._apply_unicore_function("uniq")

    def flatten(self, depth=None):
        return self._apply_unicore_function("flatten", depth=depth)

    def invoke(self, method_name, *args, **kwargs):
        new_collection = []
        for item in self.collection:
            method = getattr(item, method_name, None)
            if callable(method):
                new_collection.append(method(*args, **kwargs))
            else:
                raise AttributeError(
                    f"Item '{item}' does not have a callable method '{method_name}'"
                )
        return UniCoreFWWrapper(new_collection)

    def value(self):
        return self.collection

    def first(self, n=1):
        return self._apply_unicore_function("first", n)

    def last(self, n=1):
        return self._apply_unicore_function("last", n)

    def sort(self, key=None, reverse=False):
        new_collection = sorted(self.collection, key=key, reverse=reverse)
        return UniCoreFWWrapper(new_collection)

    def compact(self):
        return self._apply_unicore_function("compact")

    def difference(self, *others):
        return self._apply_unicore_function("difference", *others)

    def intersection(self, *others):
        return self._apply_unicore_function("intersection", *others)

    def union(self, *others):
        return self._apply_unicore_function("union", *others)

    def shuffle(self):
        return self._apply_unicore_function("shuffle")

    def zip(self, *arrays):
        return self._apply_unicore_function("zip", *arrays)

    def unzip(self):
        return self._apply_unicore_function("unzip")

    def unique(self):
        return self._apply_unicore_function("uniq")

    def without(self, *values):
        return self._apply_unicore_function("without", *values)

    def keys(self):
        return self._apply_unicore_function("keys")

    def values(self):
        return self._apply_unicore_function("values")

    def extend(self, *sources):
        return self._apply_unicore_function("extend", *sources)

    def clone(self):
        return self._apply_unicore_function("clone")

    def has(self, key):
        return self._apply_unicore_function("has", key)

    def invert(self):
        return self._apply_unicore_function("invert")

    def is_string(self):
        return self._apply_unicore_function("is_string")

    def is_array(self):
        return self._apply_unicore_function("is_array")

    def is_object(self):
        return self._apply_unicore_function("is_object")

    def is_equal(self, other):
        return self._apply_unicore_function("is_equal", other)

    def tap(self, interceptor):
        interceptor(self.collection)
        return self

    def noop(self):
        return self._apply_unicore_function("noop")

    def all_keys(self):
        return self._apply_unicore_function("all_keys")

    def pairs(self):
        return self._apply_unicore_function("pairs")

    def rest(self, n=1):
        return self._apply_unicore_function("rest", n)

    def initial(self, n=1):
        return self._apply_unicore_function("initial", n)

    def times(self, n, func):
        return self._apply_unicore_function("times", n, func)

    def unique_id(self, prefix=""):
        return self._apply_unicore_function("unique_id", prefix)

    def escape(self, string):
        return self._apply_unicore_function("escape", string)

    def unescape(self, string):
        return self._apply_unicore_function("unescape", string)

    def now(self):
        return self._apply_unicore_function("now")

    def memoize(self, func):
        return self._apply_unicore_function("memoize", func)

    def bind(self, func, context, *args):
        return self._apply_unicore_function("bind", func, context, *args)

    def partial(self, func, *args):
        return self._apply_unicore_function("partial", func, *args)

    def throttle(self, func, wait):
        return self._apply_unicore_function("throttle", func, wait)

    def debounce(self, func, wait):
        return self._apply_unicore_function("debounce", func, wait)

    def once(self, func):
        """Returns a function that can be called once, returning None on subsequent calls."""
        return self._apply_unicore_function("once", func)

    def after(self, times, func):
        """Returns a function that will only run after it's been called a specified number of times."""
        return self._apply_unicore_function("after", times, func)

    def before(self, times, func):
        return self._apply_unicore_function("before", times, func)

    def wrap(self, func, wrapper):
        return self._apply_unicore_function("wrap", func, wrapper)

    def constant(self, value):
        return self._apply_unicore_function("constant", value)

    def matches(self, attrs):
        return self._apply_unicore_function("matches", attrs)

    def matcher(self, attrs):
        return self._apply_unicore_function("matcher", attrs)

    def property(self, prop_name):
        return self._apply_unicore_function("property", prop_name)

    def property_of(self, obj):
        return self._apply_unicore_function("property_of", obj)

    def is_match(self, obj, attrs):
        return self._apply_unicore_function("is_match", obj, attrs)

    def is_undefined(self, obj):
        return self._apply_unicore_function("is_undefined", obj)

    def is_null(self, obj):
        return self._apply_unicore_function("is_null", obj)

    def is_boolean(self, obj):
        return self._apply_unicore_function("is_boolean", obj)

    def is_number(self, obj):
        return self
