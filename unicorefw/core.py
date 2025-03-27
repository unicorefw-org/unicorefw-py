"""
Core classes for UniCoreFW - The Universal Core Utility Library.

This module contains the main UniCoreFW class and UniCoreFWWrapper which provide
the foundation for the library's functionality.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info
"""

# import threading
# import time
import inspect
# import sys

# Import function categories
from . import array
from . import object
from . import function
from . import utils
from . import types
from . import security
from . import template

class UniCoreFW:
    """
    The main class providing static utility methods.
    
    This class serves as the primary access point for all UniCoreFW utility functions.
    It can be used directly via static methods or by creating an instance with a collection.
    """
    _id_counter = 0  # Initialize the counter

    def __init__(self, collection):
        """
        Initialize a new UniCoreFW instance.
        
        Args:
            collection: The collection to wrap with UniCoreFWWrapper
        """
        self._version = "1.0.3"
        self._name = "UniCoreFW"
        self._author = "Kenny Ngo"
        self._description = "Universal Core Utility Library"
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
        for module in [array, object, function, utils, types, security, template]:
            if hasattr(module, function_name):
                func = getattr(module, function_name)
                break
        
        # If not found, check if it's a method of the collection
        if func is None and hasattr(self.collection, function_name):
            method = getattr(self.collection, function_name)
            if callable(method):
                result = method(*args, **kwargs)
                if isinstance(result, (list, tuple, set)):
                    return UniCoreFWWrapper(result)
                return result
        
        # If function was found in a module, call it
        if func is not None and callable(func):
            result = func(self.collection, *args, **kwargs)
            if isinstance(result, (list, tuple, set)):
                return UniCoreFWWrapper(result)
            return result
        
        # Function not found
        raise AttributeError(
            f"'unicore' and Python do not have a callable function named '{function_name}'"
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
setattr(UniCoreFW, 'max', staticmethod(utils.max_value))
setattr(UniCoreFW, 'min', staticmethod(utils.min_value))

# Attach all functions from modules to UniCoreFW as static methods
for module in [array, object, function, utils, types, security, template]:
    for name, func in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith('_'):
            setattr(UniCoreFW, name, staticmethod(func))

# Dynamically create wrapper methods for UniCoreFWWrapper
for module in [array, object, function, utils, types]:
    for name, func in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith('_') and not hasattr(UniCoreFWWrapper, name):
            def create_wrapper_method(func_name):
                def wrapper_method(self, *args, **kwargs):
                    return self._apply_unicore_function(func_name, *args, **kwargs)
                return wrapper_method
            
            wrapper_method = create_wrapper_method(name)
            setattr(UniCoreFWWrapper, name, wrapper_method)




