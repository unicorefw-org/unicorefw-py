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

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Dict, Tuple

# Import function categories
from . import array
from . import object as object_module
from . import string
from . import crypto
from . import function
from . import utils
from . import types
from . import security
from . import template
from . import db


_MODULES_IN_ORDER = [
    array,
    object_module,
    string,
    crypto,
    function,
    utils,
    types,
    security,
    template,
    db
]

# Note: UniCoreFWWrapper intentionally wraps strings as chainable values as well.
_CHAINABLE_RESULT_TYPES: Tuple[type, ...] = (str, dict, list, tuple, set)

# Registry of exported UniCoreFW functions. First match wins according to _MODULES_IN_ORDER.
# Built once at import time for O(1) runtime dispatch.
_FUNCTION_REGISTRY: Dict[str, Callable[..., Any]] = {}


class UniCoreFW:
    """
    The main class providing static utility methods.

    Use:
      - Static calls: UniCoreFW.map([1, 2, 3], func)
      - Chaining: UniCoreFW([1, 2, 3]).map(func).filter(...).value()

    Note:
        Instance attribute access intentionally prefers the wrapped UniCoreFWWrapper
        over UniCoreFW's static methods, to make chaining ergonomic and predictable.
    """

    _name = "UniCoreFW"
    _author = "Kenny Ngo"
    _email = "kenny@unicorefw.org"
    _description = "Universal Core Utility Library"
    _version = "1.1.2"  # Semantic version
    _id_counter = 0  # Reserved for future use.

    def __init__(self, collection: Any):
        self.wrapper = UniCoreFWWrapper(collection)

    def __getattribute__(self, item: str) -> Any:
        """
        Prefer wrapper attributes for instances (so `.map(...)` chains correctly).

        This fixes a subtle but important Python behavior: `__getattr__` is only called
        when normal lookup fails, but UniCoreFW attaches many static methods (e.g., `map`)
        to the class, which would otherwise shadow wrapper methods on instances.
        """
        if item == "wrapper" or item.startswith("_"):
            return object.__getattribute__(self, item)

        wrapper = object.__getattribute__(self, "wrapper")
        try:
            return getattr(wrapper, item)
        except AttributeError:
            return object.__getattribute__(self, item)

    def __call__(self, collection: Any) -> "UniCoreFWWrapper":
        return UniCoreFWWrapper(collection)

    @classmethod
    def _(cls, collection: Any) -> "UniCoreFW":
        return cls(collection)

    @staticmethod
    def _create_wrapper_method(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Create a chainable wrapper method that applies `func` to the wrapped collection.

        This avoids per-call module scanning by binding the target callable at import time.
        """
        @functools.wraps(func)
        def wrapper_method(self: "UniCoreFWWrapper", *args: Any, **kwargs: Any) -> Any:
            return self._apply_callable(func, *args, **kwargs)

        return wrapper_method


class UniCoreFWWrapper:
    """
    Wrapper class that provides method chaining for collections.

    This class wraps a collection (list, dict, str, etc.) and provides chainable
    methods for manipulating the collection using UniCoreFW functions.
    """

    def __init__(self, collection: Any):
        self.collection = collection

    @staticmethod
    def _is_chainable_result(value: Any) -> bool:
        # Keep behavior compatible with existing versions.
        return isinstance(value, _CHAINABLE_RESULT_TYPES)

    def _wrap_result(self, result: Any) -> Any:
        """
        Wrap `result` in a UniCoreFWWrapper if it is a supported chainable result type.

        Optimization:
            If the function returns the same object instance already wrapped by `self.collection`,
            return `self` to avoid allocating a new wrapper.
        """
        if isinstance(result, UniCoreFWWrapper):
            return result
        if self._is_chainable_result(result):
            if result is self.collection:
                return self
            return UniCoreFWWrapper(result)
        return result

    def _apply_callable(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        return self._wrap_result(func(self.collection, *args, **kwargs))

    def _apply_unicore_function(self, function_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Apply a UniCoreFW function (by name) to the wrapped collection.

        This method uses a prebuilt function registry for O(1) lookup.
        """
        func = _FUNCTION_REGISTRY.get(function_name)
        if func is not None:
            return self._apply_callable(func, *args, **kwargs)

        # Fallback to underlying collection method (mainly for explicit/internal use).
        method = getattr(self.collection, function_name, None)
        if callable(method):
            return self._wrap_result(method(*args, **kwargs))

        raise AttributeError(
            f"'unicorefw' and Python do not have a callable function named '{function_name}'"
        )

    def value(self) -> Any:
        """Return the underlying wrapped value."""
        return self.collection

    def chain(self) -> "UniCoreFWWrapper":
        """Return self to support fluent chaining."""
        return self


def _build_function_registry() -> None:
    """
    Populate _FUNCTION_REGISTRY and attach module functions onto UniCoreFW and UniCoreFWWrapper.

    - First module in _MODULES_IN_ORDER wins on name collisions.
    - Wrapper methods do NOT overwrite core UniCoreFWWrapper methods like `value` and `chain`.
    - Functions are bound directly into wrapper methods for fast runtime dispatch.
    """
    for module in _MODULES_IN_ORDER:
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_"):
                continue

            # Avoid accidentally exporting imported/re-exported functions from other modules.
            if getattr(func, "__module__", None) != module.__name__:
                continue

            if name in _FUNCTION_REGISTRY:
                continue

            _FUNCTION_REGISTRY[name] = func

            # Attach chainable wrapper method (without overriding existing wrapper API)
            if not hasattr(UniCoreFWWrapper, name):
                setattr(UniCoreFWWrapper, name, UniCoreFW._create_wrapper_method(func))

            # Attach static utility method (without overriding existing UniCoreFW API)
            if not hasattr(UniCoreFW, name):
                setattr(UniCoreFW, name, staticmethod(func))

    # Resolve conflicts between Python builtins and UniCoreFW's max_value/min_value:
    setattr(UniCoreFW, "max", staticmethod(utils.max_value))
    setattr(UniCoreFW, "min", staticmethod(utils.min_value))

    # Optional (non-breaking): add wrapper aliases for fluent chaining.
    if not hasattr(UniCoreFWWrapper, "max"):
        setattr(UniCoreFWWrapper, "max", UniCoreFW._create_wrapper_method(utils.max_value))
    if not hasattr(UniCoreFWWrapper, "min"):
        setattr(UniCoreFWWrapper, "min", UniCoreFW._create_wrapper_method(utils.min_value))


_build_function_registry()