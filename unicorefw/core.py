"""
File: unicorefw/core.py
Core classes for UniCoreFW - The Universal Core Utility Library.

This module contains the main UniCoreFW class and UniCoreFWWrapper which provide
the foundation for the library's functionality.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""

# import threading
# import time
# import sys
import inspect


# Import function categories
from . import array
from . import object
from . import string
from . import crypto
from . import function
from . import utils
from . import types
from . import security
from . import template

_MODULES_IN_ORDER = [
    array,
    object,
    string,
    crypto,
    function,
    utils,
    types,
    security,
    template
]

class UniCoreFW:
    """
    The main class providing static utility methods.

    This class serves as the primary access point for all UniCoreFW utility functions.
    It can be used directly via static methods or by creating an instance with a collection.
    """
    _name = "UniCoreFW"
    _author = "Kenny Ngo"
    _email = "kenny@unicorefw.org"
    _description = "Universal Core Utility Library"
    _version = "1.1.1"
    _id_counter = 0  # Initialize the counter

    def __init__(self, collection):
        """
        Initialize a new UniCoreFW instance.

        Args:
            collection: The collection to wrap with UniCoreFWWrapper
        """
        self.wrapper = UniCoreFWWrapper(collection)

    def __getattr__(self, item):
        """
        Delegate attribute access to the wrapped instance or UniCoreFW static methods.

        Args:
            item: The attribute name to access

        Returns:
            The requested attribute

        Raises:
            AttributeError: If the attribute doesn't exist
        """
        # Delegate attribute access to the wrapped instance
        if hasattr(self.wrapper, item):
            return getattr(self.wrapper, item)
        elif hasattr(UniCoreFW, item):
            return getattr(UniCoreFW, item)
        raise AttributeError(f"'UniCoreFW' object has no attribute '{item}'")
    

    def __call__(self, collection):
        """
        Return a new UniCoreFWWrapper instance when called.

        Args:
            collection: The collection to wrap

        Returns:
            UniCoreFWWrapper: A new wrapper instance
        """
        return UniCoreFWWrapper(collection)

    # Optional factory method for creating an instance
    @classmethod
    def _(cls, collection):
        """
        Factory method to create a UniCoreFW instance.

        Args:
            collection: The collection to wrap

        Returns:
            UniCoreFW: A new UniCoreFW instance
        """
        return cls(collection)

    @staticmethod
    def _create_wrapper_method(func_name):
        def wrapper_method(self, *args, **kwargs):
            return self._apply_unicore_function(func_name, *args, **kwargs)

        return wrapper_method
    
class UniCoreFWWrapper:
    """
    Wrapper class that provides method chaining for collections.

    This class wraps a collection (list, dict, etc.) and provides chainable
    methods for manipulating the collection.
    """

    def __init__(self, collection):
        """
        Initialize a new UniCoreFWWrapper instance.

        Args:
            collection (iterable): The collection of items to be wrapped and manipulated
                                  using the UniCoreFW functions.
        """
        self.collection = collection

    def _apply_unicore_function(self, function_name, *args, **kwargs):
        """
        Apply a UniCoreFW function to the wrapped collection.

        Args:
            function_name (str): The name of the function to apply
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function, wrapped in UniCoreFWWrapper if it's a collection

        Raises:
            AttributeError: If the function doesn't exist
        """
        # First check if the function exists in any of the modules
        func = None
        for module in _MODULES_IN_ORDER:
            if hasattr(module, function_name):
                func = getattr(module, function_name)
                break

        # If not found, check if it's a method of the collection
        if func is None and hasattr(self.collection, function_name):
            method = getattr(self.collection, function_name)
            if callable(method):
                result = method(*args, **kwargs)
                if isinstance(result, (str, dict, list, tuple, set)):
                    return UniCoreFWWrapper(result)
                return result

        # If function was found in a module, call it
        if func is not None and callable(func):
            result = func(self.collection, *args, **kwargs)
            if isinstance(result, (str, dict, list, tuple, set)):
                return UniCoreFWWrapper(result)
            return result

        # Function not found
        raise AttributeError(
            f"'unicorefw' and Python do not have a callable function named '{function_name}'"
        )

    def value(self):
        """
        Get the underlying collection.

        Returns:
            The wrapped collection
        """
        return self.collection

    def chain(self):
        """
        Start a chain of operations.

        Returns:
            UniCoreFWWrapper: Self for chaining
        """
        return self


# Resolving conflicts between python max and min
setattr(UniCoreFW, "max", staticmethod(utils.max_value))
setattr(UniCoreFW, "min", staticmethod(utils.min_value))

# Attach all functions from modules to UniCoreFW as static methods
for module in _MODULES_IN_ORDER:
    for name, func in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith("_"):
            wrapper_method = UniCoreFW._create_wrapper_method(name)
            setattr(UniCoreFWWrapper, name, wrapper_method)
            # 👇 prevent later modules from overriding earlier ones
            if not hasattr(UniCoreFW, name):
                setattr(UniCoreFW, name, staticmethod(func))
