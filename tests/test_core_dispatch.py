"""Contracts for deterministic core dispatch and wrapper metadata."""

from __future__ import annotations

import importlib
import inspect
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

import unicorefw
from unicorefw import UniCoreFW, UniCoreFWWrapper, _

array_module = importlib.import_module("unicorefw.array")
core_module = importlib.import_module("unicorefw.core")
function_module = importlib.import_module("unicorefw.function")
object_module = importlib.import_module("unicorefw.object")
types_module = importlib.import_module("unicorefw.types")
utils_module = importlib.import_module("unicorefw.utils")


def test_direct_static_and_factory_static_calls_share_core_callable_identity():
    assert UniCoreFW.map is _.map
    assert UniCoreFW.map is array_module.map
    assert UniCoreFW.invoke is object_module.invoke
    assert UniCoreFW.now is function_module.now
    assert unicorefw.now is utils_module.now


def test_direct_static_and_factory_static_calls_preserve_metadata():
    for function in (UniCoreFW.map, _.map):
        assert function.__name__ == array_module.map.__name__
        assert function.__doc__ == array_module.map.__doc__
        assert function.__annotations__ == array_module.map.__annotations__
        assert inspect.signature(function) == inspect.signature(array_module.map)


def test_wrapper_map_characterization_preserves_bound_signature():
    wrapper_method = UniCoreFWWrapper.map
    bound_method = _([1, 2]).map # type: ignore
    direct_signature = inspect.signature(array_module.map)
    expected_bound_signature = direct_signature.replace(
        parameters=tuple(direct_signature.parameters.values())[1:]
    )

    assert wrapper_method.__wrapped__ is array_module.map
    assert wrapper_method.__name__ == array_module.map.__name__
    assert wrapper_method.__doc__ == array_module.map.__doc__
    assert wrapper_method.__annotations__ == array_module.map.__annotations__
    assert inspect.signature(bound_method) == expected_bound_signature


def test_chain_registry_excludes_functions_without_a_wrapped_input():
    assert len(core_module._FUNCTION_REGISTRY) == 350
    assert "now" not in core_module._FUNCTION_REGISTRY
    assert "noop" not in core_module._FUNCTION_REGISTRY
    assert "generate_key" not in core_module._FUNCTION_REGISTRY

    for function_name in ("now", "noop", "generate_key"):
        assert callable(getattr(UniCoreFW, function_name))
        assert callable(getattr(_, function_name))
        assert not hasattr(UniCoreFWWrapper, function_name)


def test_lazy_encryption_functions_remain_chainable():
    for function_name in ("encrypt_string", "decrypt_string"):
        assert function_name in core_module._FUNCTION_REGISTRY
        assert hasattr(UniCoreFWWrapper, function_name)
        assert callable(getattr(UniCoreFW, function_name))


def test_runtime_setup_uses_declarations_without_reflection_scans():
    core_source = Path(core_module.__file__).read_text(encoding="utf-8") # type: ignore
    package_source = Path(unicorefw.__file__).read_text(encoding="utf-8")

    assert "import inspect" not in core_source
    assert "inspect.getmembers" not in core_source
    assert "_MODULES_IN_ORDER" not in core_source
    assert "dir(utility_class)" not in package_source


@pytest.mark.parametrize(
    ("module_name", "function_name", "message"),
    [
        ("missing", "identity", "configured core module missing"),
        ("utils", "missing", "configured core export utils.missing"),
    ],
)
def test_declared_loader_rejects_missing_configuration(
    module_name,
    function_name,
    message,
):
    with pytest.raises(RuntimeError, match=message):
        core_module._load_declared_function(module_name, function_name)


def test_declared_loader_rejects_non_callable_without_disclosing_value(
    monkeypatch,
):
    monkeypatch.setattr(core_module.utils, "identity", "private-sentinel")

    with pytest.raises(RuntimeError, match="is not callable") as caught:
        core_module._load_declared_function("utils", "identity")

    assert "private-sentinel" not in str(caught.value)


def test_rebuilding_registry_preserves_callable_identities():
    registry_before = dict(core_module._FUNCTION_REGISTRY)
    static_before = UniCoreFW.map
    wrapper_before = UniCoreFWWrapper.map
    lazy_static_before = UniCoreFW.encrypt_string
    lazy_wrapper_before = UniCoreFWWrapper.encrypt_string

    core_module._build_function_registry()
    core_module._build_function_registry()

    assert core_module._FUNCTION_REGISTRY == registry_before
    assert UniCoreFW.map is static_before
    assert UniCoreFWWrapper.map is wrapper_before
    assert UniCoreFW.encrypt_string is lazy_static_before
    assert UniCoreFWWrapper.encrypt_string is lazy_wrapper_before


def test_unicore_instance_dispatches_wrapper_static_and_factory_paths():
    instance = UniCoreFW([1, 2]) # type: ignore

    assert isinstance(instance.wrapper, UniCoreFWWrapper) # type: ignore
    assert instance._version == UniCoreFW._version
    assert instance.map(lambda value: value + 1).value() == [2, 3]
    assert isinstance(instance.now(), int)
    assert instance("value").value() == "value"
    assert isinstance(UniCoreFW._([1]), UniCoreFW) # type: ignore


def test_wrapper_result_handling_covers_supported_and_scalar_values():
    wrapper = UniCoreFWWrapper([1]) # type: ignore
    existing_wrapper = UniCoreFWWrapper([2]) # type: ignore

    assert wrapper._wrap_result(existing_wrapper) is existing_wrapper
    assert wrapper._wrap_result(wrapper.collection) is wrapper

    wrapped_result = wrapper._wrap_result([2])
    assert isinstance(wrapped_result, UniCoreFWWrapper) # type: ignore
    assert wrapped_result.value() == [2]
    assert wrapper._wrap_result(1) == 1
    assert wrapper.chain() is wrapper


def test_private_name_dispatch_uses_registry_collection_and_error_paths():
    values = UniCoreFWWrapper([1]) # type: ignore
    assert values._apply_unicore_function("identity") is values

    text = UniCoreFWWrapper("hello") # type: ignore
    assert text._apply_unicore_function("upper").value() == "HELLO"

    with pytest.raises(AttributeError, match="do not have"):
        values._apply_unicore_function("missing")


def test_lazy_static_proxy_resolves_and_caches_declared_function():
    proxy = core_module._create_lazy_static_method("types", "is_string")

    assert proxy("value") is True
    assert UniCoreFW.is_string is types_module.is_string
