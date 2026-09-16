"""
UniCoreFW - Universal Core Utility Library
==========================================

The package root is intentionally lightweight. Public compatibility names are
resolved from an explicit ownership map only when first accessed.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""

from importlib import import_module as _import_module

from ._exports import PUBLIC_SUBMODULES as _PUBLIC_SUBMODULES
from ._exports import ROOT_EXPORTS as _ROOT_EXPORTS
from ._metadata import AUTHOR as __author__  # noqa: F401
from ._metadata import AUTHOR_EMAIL as __email__  # noqa: F401
from ._metadata import PACKAGE_DISPLAY_NAME as DISPLAY_NAME  # noqa: F401
from ._metadata import VERSION as __version__  # noqa: F401

_CORE_EXPORT_NAMES = frozenset(("UniCoreFW", "UniCoreFWWrapper", "_"))


def _load_core_exports():
    core_module = _import_module(".core", __package__)
    from ._core_registry import STATIC_EXPORT_NAMES

    utility_class = core_module.UniCoreFW
    wrapper_class = core_module.UniCoreFWWrapper

    def factory(collection):
        """Return a chainable :class:`UniCoreFWWrapper` for ``collection``."""
        return wrapper_class(collection)

    factory.__name__ = "_"
    factory.__qualname__ = "_"
    for function_name in STATIC_EXPORT_NAMES:
        function = getattr(utility_class, function_name)
        if not callable(function):
            raise RuntimeError(  # noqa: TRY004
                f"configured static export {function_name} is not callable"
            )
        setattr(factory, function_name, function)

    globals().update(
        {
            "UniCoreFW": utility_class,
            "UniCoreFWWrapper": wrapper_class,
            "_": factory,
        }
    )
    # These module names intentionally collide with historical root functions.
    # Import machinery adds the modules to the package; lazy export resolution
    # must retain the established callable surface.
    globals().pop("object", None)
    globals().pop("template", None)


def __getattr__(name):
    """Resolve only declared compatibility exports and public submodules."""
    if name in _CORE_EXPORT_NAMES:
        _load_core_exports()
        return globals()[name]

    module_name = _ROOT_EXPORTS.get(name)
    if module_name is not None:
        module = _import_module(f".{module_name}", __package__)
        try:
            value = getattr(module, name)
        except AttributeError as exc:
            raise AttributeError(
                f"configured unicorefw export {name!r} is unavailable"
            ) from exc
        globals()[name] = value
        return value

    if name in _PUBLIC_SUBMODULES:
        module = _import_module(f".{name}", __package__)
        globals()[name] = module
        return module

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """Include declared lazy exports in interactive discovery."""
    return sorted(
        set(globals())
        | _CORE_EXPORT_NAMES
        | set(_ROOT_EXPORTS)
        | set(_PUBLIC_SUBMODULES)
    )


__all__ = ["UniCoreFW", "UniCoreFWWrapper", "_"] # type: ignore
