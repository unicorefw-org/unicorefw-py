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
import importlib
from collections.abc import Callable
from typing import Any

from ._core_registry import (
    COMPATIBILITY_ALIASES,
    CORE_EXPORTS_BY_MODULE,
    LAZY_CHAIN_EXPORTS,
    LAZY_STATIC_EXPORTS,
)
from ._metadata import AUTHOR, AUTHOR_EMAIL, DESCRIPTION, PACKAGE_DISPLAY_NAME, VERSION

array = importlib.import_module(".array", __package__)
object_module = importlib.import_module(".object", __package__)
string = importlib.import_module(".string", __package__)
function = importlib.import_module(".function", __package__)
utils = importlib.import_module(".utils", __package__)
types = importlib.import_module(".types", __package__)
security = importlib.import_module(".security", __package__)
template = importlib.import_module(".template", __package__)


_CORE_MODULES = {
    "array": array,
    "object": object_module,
    "string": string,
    "function": function,
    "utils": utils,
    "types": types,
    "security": security,
    "template": template,
}

# Note: UniCoreFWWrapper intentionally wraps strings as chainable values as well.
_CHAINABLE_RESULT_TYPES: tuple[type, ...] = (str, dict, list, tuple, set)

# Registry of declared chain functions, built once for O(1) name dispatch.
_FUNCTION_REGISTRY: dict[str, Callable[..., Any]] = {}
_object_getattribute = object.__getattribute__


def _load_declared_function(
    module_name: str,
    function_name: str,
) -> Callable[..., Any]:
    try:
        module = _CORE_MODULES[module_name]
    except KeyError as exc:
        raise RuntimeError(
            f"configured core module {module_name} is unavailable"
        ) from exc
    try:
        function = getattr(module, function_name)
    except AttributeError as exc:
        raise RuntimeError(
            f"configured core export {module_name}.{function_name} is unavailable"
        ) from exc
    if not callable(function):
        raise RuntimeError(  # noqa: TRY004
            f"configured core export {module_name}.{function_name} is not callable"
        )
    return function


def _load_public_function(module_name: str, function_name: str) -> Callable[..., Any]:
    module = importlib.import_module(f".{module_name}", __package__)
    function = getattr(module, function_name)
    if not callable(function):
        raise RuntimeError(  # noqa: TRY004
            f"configured lazy export {module_name}.{function_name} is not callable"
        )
    return function


def _create_lazy_static_method(
    module_name: str,
    function_name: str,
) -> Callable[..., Any]:
    def lazy_method(*args: Any, **kwargs: Any) -> Any:
        function = _load_public_function(module_name, function_name)
        setattr(UniCoreFW, function_name, staticmethod(function))
        return function(*args, **kwargs)

    lazy_method.__name__ = function_name
    lazy_method.__qualname__ = f"UniCoreFW.{function_name}"
    lazy_method.__doc__ = (
        f"Lazy compatibility proxy for ``unicorefw.{module_name}." f"{function_name}``."
    )
    return lazy_method


def _create_lazy_wrapper_method(
    module_name: str,
    function_name: str,
) -> Callable[..., Any]:
    def lazy_wrapper(
        self: UniCoreFWWrapper,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        function = _load_public_function(module_name, function_name)
        return self._apply_callable(function, *args, **kwargs)

    lazy_wrapper.__name__ = function_name
    lazy_wrapper.__qualname__ = f"UniCoreFWWrapper.{function_name}"
    lazy_wrapper.__doc__ = (
        f"Lazy chain proxy for ``unicorefw.{module_name}.{function_name}``."
    )
    return lazy_wrapper


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

    _name = PACKAGE_DISPLAY_NAME
    _author = AUTHOR
    _email = AUTHOR_EMAIL
    _description = DESCRIPTION
    _version = VERSION  # Semantic version
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
            return _object_getattribute(self, item)

        wrapper = _object_getattribute(self, "wrapper")
        try:
            return getattr(wrapper, item)
        except AttributeError:
            return _object_getattribute(self, item)

    def __call__(self, collection: Any) -> UniCoreFWWrapper:
        return UniCoreFWWrapper(collection)

    @classmethod
    def _(cls, collection: Any) -> UniCoreFW:
        return cls(collection)

    @staticmethod
    def _create_wrapper_method(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Create a chainable wrapper method that applies `func` to the wrapped collection.

        This avoids per-call module scanning by binding the target callable at import time.
        """

        @functools.wraps(func)
        def wrapper_method(self: UniCoreFWWrapper, *args: Any, **kwargs: Any) -> Any:
            result = func(self.collection, *args, **kwargs)
            return self._wrap_result(result)

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

    def _apply_callable(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        return self._wrap_result(func(self.collection, *args, **kwargs))

    def _apply_unicore_function(
        self, function_name: str, *args: Any, **kwargs: Any
    ) -> Any:
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

    def chain(self) -> UniCoreFWWrapper:
        """Return self to support fluent chaining."""
        return self


def _build_function_registry() -> None:
    """
    Attach declared static functions and chainable wrapper methods.

    - Generated ownership preserves historical name-collision behavior.
    - Wrapper methods do NOT overwrite core UniCoreFWWrapper methods like `value` and `chain`.
    - Functions are bound directly into wrapper methods for fast runtime dispatch.
    """
    for (
        module_name,
        packed_function_names,
        packed_static_only_names,
    ) in CORE_EXPORTS_BY_MODULE:
        static_only_names = frozenset(packed_static_only_names.split())
        for function_name in packed_function_names.split():
            declared_function = _load_declared_function(
                module_name,
                function_name,
            )
            if not hasattr(UniCoreFW, function_name):
                setattr(
                    UniCoreFW,
                    function_name,
                    staticmethod(declared_function),
                )
            if function_name in static_only_names:
                continue
            if function_name not in _FUNCTION_REGISTRY:
                _FUNCTION_REGISTRY[function_name] = declared_function
            if not hasattr(UniCoreFWWrapper, function_name):
                setattr(
                    UniCoreFWWrapper,
                    function_name,
                    UniCoreFW._create_wrapper_method(declared_function),
                )

    for (
        public_name,
        module_name,
        target_name,
        chainable,
    ) in COMPATIBILITY_ALIASES:
        declared_function = _load_declared_function(module_name, target_name)
        if not hasattr(UniCoreFW, public_name):
            setattr(
                UniCoreFW,
                public_name,
                staticmethod(declared_function),
            )
        if chainable and not hasattr(UniCoreFWWrapper, public_name):
            setattr(
                UniCoreFWWrapper,
                public_name,
                UniCoreFW._create_wrapper_method(declared_function),
            )

    for module_name, packed_function_names in LAZY_CHAIN_EXPORTS:
        for function_name in packed_function_names.split():
            static_proxy = _FUNCTION_REGISTRY.get(function_name)
            if static_proxy is None:
                static_proxy = _create_lazy_static_method(
                    module_name,
                    function_name,
                )
                _FUNCTION_REGISTRY[function_name] = static_proxy
            if not hasattr(UniCoreFW, function_name):
                setattr(UniCoreFW, function_name, staticmethod(static_proxy))
            if not hasattr(UniCoreFWWrapper, function_name):
                setattr(
                    UniCoreFWWrapper,
                    function_name,
                    _create_lazy_wrapper_method(module_name, function_name),
                )

    # Database and ORM helper functions stay available as static compatibility
    # calls but are intentionally not registered as collection chain methods.
    for module_name, packed_function_names in LAZY_STATIC_EXPORTS:
        for function_name in packed_function_names.split():
            if not hasattr(UniCoreFW, function_name):
                setattr(
                    UniCoreFW,
                    function_name,
                    staticmethod(
                        _create_lazy_static_method(module_name, function_name)
                    ),
                )


_build_function_registry()
