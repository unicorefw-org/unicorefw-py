"""Regression tests for the lazy package-root import contract."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

import unicorefw
from scripts import benchmark_imports
from scripts.benchmark_imports import ImportBudgetError, benchmark_import
from unicorefw import UniCoreFW, UniCoreFWWrapper, _
from unicorefw import core as core_module
from unicorefw._core_registry import STATIC_EXPORT_NAMES
from unicorefw._exports import PUBLIC_EXPORTS_BY_MODULE

ROOT = Path(__file__).resolve().parents[1]


def _isolated_python(source: str):
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-c", source],
        capture_output=True,
        check=True,
        cwd=ROOT,
        env=environment,
        text=True,
        timeout=30,
    )
    return json.loads(completed.stdout)


def test_bare_root_import_is_lightweight_and_side_effect_free():
    result = _isolated_python(
        """
import json
import logging
import sys
import threading

events = []
def audit(event, arguments):
    if event in {"socket.connect", "subprocess.Popen", "os.system"}:
        events.append(event)

sys.addaudithook(audit)
threads_before = threading.active_count()
handlers_before = tuple(logging.getLogger().handlers)
import unicorefw
optional = {
    "cryptography", "openpyxl", "pandas", "psycopg2",
    "pymongo", "pymysql", "redis", "sqlalchemy",
}
print(json.dumps({
    "core_loaded": "unicorefw.core" in sys.modules,
    "events": events,
    "handlers_changed": tuple(logging.getLogger().handlers) != handlers_before,
    "name": unicorefw.__name__,
    "optional": sorted(optional & set(sys.modules)),
    "threads_changed": threading.active_count() != threads_before,
}))
"""
    )

    assert result == {
        "core_loaded": False,
        "events": [],
        "handlers_changed": False,
        "name": "unicorefw",
        "optional": [],
        "threads_changed": False,
    }


def test_core_entry_points_do_not_load_optional_dependencies():
    result = _isolated_python(
        """
import json
import sys
from unicorefw import UniCoreFW, _

assert _.map([1, 2], lambda value: value + 1) == [2, 3]
assert UniCoreFW.humanize("hello_world") == "Hello world"
optional = {
    "cryptography", "openpyxl", "pandas", "psycopg2",
    "pymongo", "pymysql", "redis", "sqlalchemy",
}
print(json.dumps({
    "optional": sorted(optional & set(sys.modules)),
    "wrapper_has_connect": hasattr(type(_([])), "connect"),
    "static_has_connect": hasattr(UniCoreFW, "connect"),
}))
"""
    )

    assert result == {
        "optional": [],
        "static_has_connect": True,
        "wrapper_has_connect": False,
    }


def test_optional_crypto_loads_only_when_called():
    result = _isolated_python(
        """
import json
import sys
from unicorefw import UniCoreFW, _

before = "cryptography" in sys.modules
key = UniCoreFW.generate_key()
token = _.encrypt_string("value", key)
plaintext = _(token).decrypt_string(key).value()
print(json.dumps({
    "after": "cryptography" in sys.modules,
    "before": before,
    "plaintext": plaintext,
    "sqlalchemy": "sqlalchemy" in sys.modules,
}))
"""
    )

    assert result == {
        "after": True,
        "before": False,
        "plaintext": "value",
        "sqlalchemy": False,
    }


def test_declared_root_exports_are_discoverable_and_cached(monkeypatch):
    assert unicorefw.__name__ == "unicorefw"
    assert "generate_key" in dir(unicorefw)
    assert unicorefw.humanize is unicorefw.humanize
    assert unicorefw.now is unicorefw.utils.now
    monkeypatch.delitem(unicorefw.__dict__, "supporter", raising=False)
    assert unicorefw.__getattr__("supporter").__name__ == "unicorefw.supporter"

    with pytest.raises(AttributeError, match="has no attribute"):
        getattr(unicorefw, "not_a_declared_export")  # noqa: B009


def test_declared_export_map_matches_implementation_modules():
    for module_name, export_names in PUBLIC_EXPORTS_BY_MODULE:
        module = __import__(f"unicorefw.{module_name}", fromlist=["*"])
        missing = sorted(name for name in export_names if not hasattr(module, name))
        assert missing == [], f"{module_name} is missing {missing}"


def test_configured_missing_export_fails_without_fallback_import(monkeypatch):
    monkeypatch.setitem(unicorefw._ROOT_EXPORTS, "missing_export", "types")

    with pytest.raises(AttributeError, match="configured unicorefw export"):
        unicorefw.__getattr__("missing_export")


def test_core_lazy_export_rejects_non_callable(monkeypatch):
    class _Module:
        invalid = 1

    monkeypatch.setattr(core_module.importlib, "import_module", lambda *args: _Module())

    with pytest.raises(RuntimeError, match="is not callable"):
        core_module._load_public_function("module", "invalid")


def test_package_factory_rejects_declared_non_callable_without_disclosure(
    monkeypatch,
):
    function_name = STATIC_EXPORT_NAMES[0]
    monkeypatch.setattr(UniCoreFW, function_name, "private-sentinel")

    with pytest.raises(RuntimeError, match="is not callable") as caught:
        unicorefw._load_core_exports()

    assert function_name in str(caught.value)
    assert "private-sentinel" not in str(caught.value)


def test_lazy_wrapper_proxy_loads_and_applies_declared_function():
    wrapper = UniCoreFWWrapper("value") # type: ignore
    proxy = core_module._create_lazy_wrapper_method("types", "is_string")

    assert proxy(wrapper) is True
    assert proxy.__name__ == "is_string"


def test_rebuilding_core_registry_is_idempotent():
    registry_before = dict(core_module._FUNCTION_REGISTRY)

    core_module._build_function_registry()

    assert core_module._FUNCTION_REGISTRY == registry_before


@pytest.mark.parametrize("runs", [True, 0, 51])
def test_import_benchmark_rejects_invalid_run_count(runs):
    with pytest.raises(ImportBudgetError, match="runs"):
        benchmark_import("unicorefw", runs=runs)


@pytest.mark.parametrize("target", ["os", "unicorefw.not-valid"])
def test_import_benchmark_rejects_unsafe_targets(target):
    with pytest.raises(ImportBudgetError, match="target"):
        benchmark_import(target, runs=1)


@pytest.mark.parametrize(
    ("keyword", "value"),
    [
        ("maximum_median_ms", True),
        ("maximum_median_ms", float("nan")),
        ("maximum_median_rss_kib", -1),
    ],
)
def test_import_benchmark_rejects_invalid_budgets(keyword, value):
    with pytest.raises(ImportBudgetError, match="finite non-negative"):
        benchmark_import("unicorefw", runs=1, **{keyword: value})


def test_import_benchmark_reports_every_policy_violation(monkeypatch):
    monkeypatch.setattr(
        benchmark_imports,
        "_run_worker",
        lambda target: {
            "duration_ms": 101,
            "optional_modules": ["sqlalchemy"],
            "rss_delta_kib": 1025,
            "side_effect_events": ["socket.connect"],
            "target": target,
        },
    )

    with pytest.raises(ImportBudgetError) as caught:
        benchmark_import(
            "unicorefw",
            runs=1,
            forbid_optional=True,
            maximum_median_ms=100,
            maximum_median_rss_kib=1024,
        )

    message = str(caught.value)
    assert "socket.connect" in message
    assert "sqlalchemy" in message
    assert "exceeds 100.000 ms" in message
    assert "exceeds 1024 KiB" in message


def test_root_import_meets_generous_local_regression_ceiling():
    summary = benchmark_import(
        "unicorefw",
        runs=3,
        forbid_optional=True,
        maximum_median_ms=500,
        maximum_median_rss_kib=20 * 1024,
    )

    assert summary["target"] == "unicorefw"
    assert summary["optional_modules"] == []
    assert summary["side_effect_events"] == []


def test_database_and_orm_functions_are_not_chain_registered():
    assert "connect" not in core_module._FUNCTION_REGISTRY
    assert "session_scope" not in core_module._FUNCTION_REGISTRY
    assert not hasattr(UniCoreFWWrapper, "connect")
    assert not hasattr(UniCoreFWWrapper, "session_scope")
    assert callable(UniCoreFW.connect)
    assert callable(UniCoreFW.session_scope)


def test_zero_argument_helpers_are_static_only():
    for function_name in ("now", "noop", "generate_key"):
        assert function_name not in core_module._FUNCTION_REGISTRY
        assert not hasattr(UniCoreFWWrapper, function_name)
        assert callable(getattr(UniCoreFW, function_name))
        assert callable(getattr(_, function_name))
