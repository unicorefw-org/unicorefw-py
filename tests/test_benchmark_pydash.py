"""Tests for the bounded pydash comparison benchmark."""

from __future__ import annotations

import argparse
import builtins
import importlib.metadata
import json
import os
import runpy
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from scripts import benchmark_pydash, benchmark_release
from unicorefw import UniCoreFW


@pytest.fixture(autouse=True)
def _restore_benchmark_target_import_state():
    prefixes = ("pydash", "unicorefw")
    original_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == prefixes[0] or name.startswith((prefixes[0] + ".", prefixes[1] + ".")) or name == prefixes[1]
    }
    original_path = list(sys.path)
    yield
    for name in list(sys.modules):
        if (
            name == prefixes[0] or name.startswith((prefixes[0] + ".", prefixes[1] + ".")) or name == prefixes[1]
        ):
            del sys.modules[name]
    sys.modules.update(original_modules)
    sys.path[:] = original_path


def _fake_pydash_import(
    monkeypatch,
    *,
    module_version="8.0.6",
    distribution_version="8.0.6",
    module_path="/opt/site-packages/pydash/__init__.py",
):
    module = SimpleNamespace(__file__=module_path, __version__=module_version)
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(
        benchmark_pydash,
        "_distribution_version",
        lambda _name: distribution_version,
    )
    monkeypatch.setattr(
        benchmark_pydash.importlib,
        "import_module",
        lambda _name: module,
    )
    return module


def _require_baseline_pydash():
    if sys.version_info < (3, 9):  # noqa: UP036
        pytest.skip("pydash 8.0.6 requires Python 3.9 or newer")
    return pytest.importorskip("pydash")


def _worker_payload():
    report = benchmark_release.WorkerReport(
        implementation="pydash",
        version="8.0.6",
        module_path="/opt/site-packages/pydash/__init__.py",
        api_count=2,
        results=[],
    )
    return benchmark_pydash.WorkerPayload(
        report=report,
        api_names=frozenset({"add", "map_"}),
        distribution_version="8.0.6",
        expected_version="8.0.6",
        baseline_overridden=False,
    )


def _case_payload(
    implementation,
    *,
    name="identity",
    status=benchmark_release.CaseStatus.BENCHMARKED,
    seconds=1e-6,
    normalized="value",
    detail="",
    expected_version="8.0.6",
):
    version = "8.0.6" if implementation == "pydash" else "1.1.5"
    module_path = (
        "/opt/site-packages/pydash/__init__.py"
        if implementation == "pydash"
        else str(benchmark_pydash.PROJECT_ROOT / "unicorefw" / "__init__.py")
    )
    report = benchmark_release.WorkerReport(
        implementation=implementation,
        version=version,
        module_path=module_path,
        api_count=1,
        results=[
            benchmark_release.CaseResult(
                name=name,
                category="utility",
                status=status,
                seconds=seconds,
                normalized=normalized,
                detail=detail,
            )
        ],
    )
    return benchmark_pydash.WorkerPayload(
        report=report,
        api_names=frozenset({name}),
        distribution_version="8.0.6" if implementation == "pydash" else "",
        expected_version=expected_version,
        baseline_overridden=expected_version != "8.0.6",
    )


def _merge_reports(pydash_payload, local_payload):
    expected_keys = frozenset(
        (result.category, result.name) for result in local_payload.report.results
    )
    return benchmark_pydash.merge_reports(
        pydash_payload,
        local_payload,
        expected_keys,
    )


def test_baseline_compatibility_partition_is_exact():
    pydash = _require_baseline_pydash()
    local_names = benchmark_release.discover_public_api_names(UniCoreFW)
    pydash_names = benchmark_release.discover_public_api_names(pydash)
    shared_names = local_names & pydash_names

    assert pydash.__version__ == benchmark_pydash.BASELINE_PYDASH_VERSION
    assert len(local_names) == 365
    assert len(pydash_names) == 365
    assert len(shared_names) == 273
    assert len(benchmark_pydash.COMPARABLE_CASE_NAMES) == 240
    assert len(benchmark_pydash.INCOMPATIBLE_REASONS) == 33
    assert not (
        benchmark_pydash.COMPARABLE_CASE_NAMES
        & set(benchmark_pydash.INCOMPATIBLE_REASONS)
    )
    assert (
        benchmark_pydash.COMPARABLE_CASE_NAMES
        | set(benchmark_pydash.INCOMPATIBLE_REASONS)
    ) == shared_names


def test_comparable_registry_contains_each_allowlisted_case_once():
    cases = benchmark_pydash.build_comparable_cases()

    assert len(cases) == 240
    assert {case.name for case in cases} == benchmark_pydash.COMPARABLE_CASE_NAMES
    assert len({(case.category, case.name) for case in cases}) == 240
    assert cases == sorted(cases, key=lambda case: (case.category, case.name))


def test_comparable_registry_filters_categories():
    cases = benchmark_pydash.build_comparable_cases(frozenset({"array"}))

    assert cases
    assert {case.category for case in cases} == {"array"}


def test_comparable_registry_filters_one_api_and_rejects_incompatible_selection():
    cases = benchmark_pydash.build_comparable_cases(api_name="map_")

    assert [(case.category, case.name) for case in cases] == [("object", "map_")]
    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="is not in the selected categories",
    ):
        benchmark_pydash.build_comparable_cases(
            frozenset({"array"}), api_name="map_"
        )


def test_comparable_registry_rejects_unknown_api():
    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="unknown API: missing",
    ):
        benchmark_pydash.build_comparable_cases(api_name="missing")


def test_comparable_registry_rejects_unknown_categories():
    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="unknown categories: missing",
    ):
        benchmark_pydash.build_comparable_cases(frozenset({"missing"}))


def test_inventory_reports_sorted_unique_and_unverified_names():
    inventory = benchmark_pydash.build_inventory(
        {"shared", "local_only"},
        {"shared", "pydash_only"},
    )

    assert inventory == {
        "local_api_count": 2,
        "pydash_api_count": 2,
        "shared_api_count": 1,
        "compatible_count": 0,
        "incompatible_shared_count": 1,
        "local_only_count": 1,
        "pydash_only_count": 1,
        "local_only_names": ["local_only"],
        "pydash_only_names": ["pydash_only"],
        "shared_names": ["shared"],
        "compatible_names": [],
        "incompatible_shared": {"shared": "not validated against pydash 8.0.6"},
    }


@pytest.mark.parametrize("mode", ["", "release", "unknown"])
def test_import_target_rejects_unknown_mode(mode):
    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="target must be 'pydash' or 'local'",
    ):
        benchmark_pydash.import_target(mode, "8.0.6")


def test_pydash_import_removes_project_paths_before_import(monkeypatch):
    seen_paths = []
    module = SimpleNamespace(
        __file__="/opt/site-packages/pydash/__init__.py",
        __version__="8.0.6",
    )
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(
        benchmark_pydash, "_distribution_version", lambda _name: "8.0.6"
    )

    def import_module(_name):
        seen_paths.extend(Path(entry or ".").resolve() for entry in sys.path)
        return module

    monkeypatch.setattr(benchmark_pydash.importlib, "import_module", import_module)

    (
        imported_module,
        imported_api,
        distribution_version,
    ) = benchmark_pydash.import_target("pydash", "8.0.6")

    assert imported_module is module
    assert imported_api is module
    assert distribution_version == "8.0.6"
    assert benchmark_pydash.PROJECT_ROOT not in seen_paths
    assert benchmark_pydash.SCRIPTS_ROOT not in seen_paths


def test_pydash_import_rejects_project_local_module(monkeypatch):
    _fake_pydash_import(
        monkeypatch,
        module_path=str(benchmark_pydash.PROJECT_ROOT / "pydash.py"),
    )

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="project-local pydash module is not allowed",
    ):
        benchmark_pydash.import_target("pydash", "8.0.6")


def test_pydash_import_rejects_module_distribution_version_disagreement(
    monkeypatch,
):
    _fake_pydash_import(monkeypatch, module_version="8.0.5")

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="pydash module version 8.0.5 differs from distribution 8.0.6",
    ):
        benchmark_pydash.import_target("pydash", "8.0.6")


def test_pydash_import_rejects_wrong_expected_version(monkeypatch):
    _fake_pydash_import(monkeypatch)

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="expected pydash 9.0.0, found 8.0.6",
    ):
        benchmark_pydash.import_target("pydash", "9.0.0")


def test_distribution_version_uses_python37_backport(monkeypatch):
    real_import = builtins.__import__
    backport = SimpleNamespace(version=lambda _name: "8.0.6")

    def import_module(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "importlib" and "metadata" in fromlist:
            raise ImportError("stdlib metadata unavailable")
        if name == "importlib_metadata":
            return backport
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_module)

    assert benchmark_pydash._distribution_version("pydash") == "8.0.6"


def test_distribution_version_rejects_missing_python37_backport(monkeypatch):
    real_import = builtins.__import__

    def import_module(name, globals=None, locals=None, fromlist=(), level=0):
        if (name == "importlib" and "metadata" in fromlist) or name == (
            "importlib_metadata"
        ):
            raise ImportError("metadata unavailable")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_module)

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="Python 3.7 requires importlib-metadata",
    ):
        benchmark_pydash._distribution_version("pydash")


def test_distribution_version_rejects_missing_pydash(monkeypatch):
    def missing(_name):
        raise importlib.metadata.PackageNotFoundError("pydash")

    monkeypatch.setattr(importlib.metadata, "version", missing)

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="pydash is not installed",
    ):
        benchmark_pydash._distribution_version("pydash")


def test_pydash_import_rejects_module_without_path(monkeypatch):
    _fake_pydash_import(monkeypatch, module_path=None) # type: ignore

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="pydash module has no filesystem path",
    ):
        benchmark_pydash.import_target("pydash", "8.0.6")


def test_local_import_rejects_module_outside_worktree(monkeypatch):
    module = SimpleNamespace(
        __file__="/opt/unicorefw/__init__.py",
        UniCoreFW=SimpleNamespace(),
    )
    monkeypatch.setattr(
        benchmark_release,
        "import_implementation",
        lambda _mode: (module, module.UniCoreFW),
    )

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="local worker imported outside the project root",
    ):
        benchmark_pydash.import_target("local", "8.0.6")


def test_local_import_resolves_to_worktree():
    module, api, distribution_version = benchmark_pydash.import_target("local", "8.0.6")

    Path(module.__file__).resolve().relative_to(benchmark_pydash.PROJECT_ROOT)
    assert api is module.UniCoreFW
    assert distribution_version == ""


def test_worker_payload_round_trip(tmp_path):
    payload = _worker_payload()
    result_path = tmp_path / "worker.json"

    benchmark_pydash.write_worker_payload(payload, result_path)

    assert benchmark_pydash.read_worker_payload(result_path) == payload


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data.pop("api_names"),
        lambda data: data.update(api_names=["add", "add"]),
        lambda data: data.update(api_names=["add", 7]),
        lambda data: data.update(api_count=1),
        lambda data: data.update(baseline_overridden=True),
    ],
)
def test_worker_payload_rejects_invalid_metadata(tmp_path, mutate):
    result_path = tmp_path / "worker.json"
    benchmark_pydash.write_worker_payload(_worker_payload(), result_path)
    data = json.loads(result_path.read_text(encoding="utf-8"))
    mutate(data)
    result_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(benchmark_pydash.PydashBenchmarkError):
        benchmark_pydash.read_worker_payload(result_path)


def test_worker_payload_rejects_malformed_json(tmp_path):
    result_path = tmp_path / "worker.json"
    result_path.write_text("{", encoding="utf-8")

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="invalid worker result",
    ):
        benchmark_pydash.read_worker_payload(result_path)


@pytest.mark.parametrize(
    "value",
    [[], 7, "not-an-object"],
)
def test_worker_payload_rejects_non_object_json(tmp_path, value):
    result_path = tmp_path / "worker.json"
    result_path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="invalid worker result",
    ):
        benchmark_pydash.read_worker_payload(result_path)


@pytest.mark.parametrize(
    "field",
    ["distribution_version", "expected_version"],
)
def test_worker_payload_rejects_non_string_versions(tmp_path, field):
    result_path = tmp_path / "worker.json"
    benchmark_pydash.write_worker_payload(_worker_payload(), result_path)
    data = json.loads(result_path.read_text(encoding="utf-8"))
    data[field] = 7
    result_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(benchmark_pydash.PydashBenchmarkError):
        benchmark_pydash.read_worker_payload(result_path)


def test_worker_payload_rejects_non_boolean_override(tmp_path):
    result_path = tmp_path / "worker.json"
    benchmark_pydash.write_worker_payload(_worker_payload(), result_path)
    data = json.loads(result_path.read_text(encoding="utf-8"))
    data["baseline_overridden"] = 1
    result_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(benchmark_pydash.PydashBenchmarkError):
        benchmark_pydash.read_worker_payload(result_path)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data["results"][0].update(seconds=None),
        lambda data: data["results"][0].update(seconds=float("nan")),
        lambda data: data["results"][0].update(seconds=True),
        lambda data: data.update(version="7.0.0"),
        lambda data: data.update(distribution_version="9.0.0"),
    ],
)
def test_worker_payload_rejects_invalid_timing_or_pydash_version(tmp_path, mutate):
    result_path = tmp_path / "worker.json"
    benchmark_pydash.write_worker_payload(_case_payload("pydash"), result_path)
    data = json.loads(result_path.read_text(encoding="utf-8"))
    mutate(data)
    result_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="invalid worker result",
    ):
        benchmark_pydash.read_worker_payload(result_path)


def test_merge_revalidates_in_memory_worker_payload():
    pydash = _case_payload("pydash", seconds=None) # type: ignore

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="benchmarked result requires a finite nonnegative timing",
    ):
        benchmark_pydash.merge_reports(
            pydash,
            _case_payload("unicorefw"),
            frozenset({("utility", "identity")}),
        )


@pytest.mark.parametrize(
    ("scope", "value", "message"),
    [
        ("payload", object(), "payload has an invalid type"),
        ("report", object(), "report has an invalid type"),
        ("report.implementation", "release", "invalid implementation"),
        ("report.version", None, "invalid version"),
        ("report.version", "", "invalid version"),
        ("report.module_path", None, "invalid module path"),
        ("report.module_path", "", "invalid module path"),
        ("report.api_count", True, "invalid API count"),
        ("report.api_count", "1", "invalid API count"),
        ("report.api_count", -1, "invalid API count"),
        ("report.results", (), "results must be a list"),
        ("api_names", {"identity"}, "API names must be a frozenset"),
        ("api_names", frozenset({1}), "API names must be a frozenset"),
        ("api_names", frozenset(), "API count does not match"),
        ("expected_version", None, "expected version is invalid"),
        ("expected_version", "8.0.6\u200b", "expected version is invalid"),
        ("distribution_version", 8, "distribution version is invalid"),
        ("baseline_overridden", 1, "baseline override is inconsistent"),
        ("baseline_overridden", True, "baseline override is inconsistent"),
        ("report.results", [object()], "result has an invalid type"),
        ("result.name", 1, "result is not a compatible case"),
        ("result.category", 1, "result is not a compatible case"),
        ("result.name", "not_allowlisted", "result is not a compatible case"),
        ("result.status", "BENCHMARKED", "result has an invalid status"),
        ("result.detail", 1, "result detail must be a string"),
        ("result.seconds", "1", "finite nonnegative timing"),
        ("result.seconds", -1, "finite nonnegative timing"),
        ("result.seconds", 10**1_000, "finite nonnegative timing"),
    ],
)
def test_worker_payload_schema_validation_is_fail_closed(scope, value, message):
    payload = _case_payload("pydash")
    if scope == "payload":
        payload = value
    elif scope == "report":
        payload = replace(payload, report=value)
    elif scope.startswith("report."):
        setattr(payload.report, scope.split(".", 1)[1], value)
    elif scope.startswith("result."):
        setattr(payload.report.results[0], scope.split(".", 1)[1], value)
    else:
        payload = replace(payload, **{scope: value})

    with pytest.raises(benchmark_pydash.PydashBenchmarkError, match=message):
        benchmark_pydash._validate_worker_payload(payload)


def test_local_worker_payload_rejects_distribution_version():
    payload = replace(
        _case_payload("unicorefw"),
        distribution_version="8.0.6",
    )

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="must not report a pydash distribution version",
    ):
        benchmark_pydash._validate_worker_payload(payload)


def test_non_benchmarked_worker_result_rejects_timing():
    payload = _case_payload(
        "pydash",
        status=benchmark_release.CaseStatus.FAILED,
        seconds=1e-6,
    )

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="non-benchmarked result must not include a timing",
    ):
        benchmark_pydash._validate_worker_payload(payload)


@pytest.mark.parametrize(
    ("status", "api_names"),
    [
        (benchmark_release.CaseStatus.BENCHMARKED, frozenset()),
        (benchmark_release.CaseStatus.MISSING, frozenset({"identity"})),
    ],
)
def test_worker_result_status_must_match_api_inventory(status, api_names):
    payload = _case_payload(
        "pydash",
        status=status,
        seconds=(1e-6 if status == benchmark_release.CaseStatus.BENCHMARKED else None), # type: ignore
    )
    payload = replace(
        payload,
        api_names=api_names,
    )
    payload.report.api_count = len(api_names)

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="result exposure disagrees with API inventory",
    ):
        benchmark_pydash._validate_worker_payload(payload)


@pytest.mark.parametrize("mode", ["pydash", "local"])
def test_worker_benchmarks_selected_compatible_category(mode, monkeypatch):
    if mode == "pydash":
        _require_baseline_pydash()
    monkeypatch.setattr(sys, "path", list(sys.path))
    payload = benchmark_pydash.run_worker(
        mode,
        expected_version="8.0.6",
        iterations=1,
        repeats=1,
        categories=frozenset({"type"}),
    )

    assert payload.api_names
    assert payload.report.results
    assert all(
        result.status == benchmark_release.CaseStatus.BENCHMARKED
        for result in payload.report.results
    )


def test_local_worker_audits_full_registry_before_filtering(monkeypatch):
    incomplete_registry = benchmark_release.build_all_cases()[:-1]
    monkeypatch.setattr(
        benchmark_release,
        "build_all_cases",
        lambda: incomplete_registry,
    )

    with pytest.raises(ValueError, match="benchmark registry coverage error"):
        benchmark_pydash.run_worker(
            "local",
            expected_version="8.0.6",
            iterations=1,
            repeats=1,
            categories=frozenset({"type"}),
        )


def test_worker_process_builds_bounded_argument_array(monkeypatch, tmp_path):
    payload = _worker_payload()
    result_path = tmp_path / "pydash.json"
    observed = {}

    def run(command, timeout):
        observed["command"] = command
        observed["timeout"] = timeout
        benchmark_pydash.write_worker_payload(payload, result_path)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(benchmark_pydash, "_run_bounded_process", run)
    args = argparse.Namespace(
        iterations=3,
        repeats=5,
        category=["type", "array"],
        expected_pydash_version="8.0.6",
        worker_timeout=30,
    )

    assert benchmark_pydash.run_worker_process("pydash", args, result_path) == payload
    assert observed["command"][:2] == [
        sys.executable,
        str(Path(benchmark_pydash.__file__).resolve()),
    ]
    assert observed["command"].count("--category") == 2
    assert observed["timeout"] == 30


def test_worker_process_rejects_timeout(monkeypatch, tmp_path):
    def timeout(command, **_kwargs):
        raise subprocess.TimeoutExpired(command, 30, output="out", stderr="err")

    monkeypatch.setattr(benchmark_pydash, "_run_bounded_process", timeout)
    args = argparse.Namespace(
        iterations=1,
        repeats=1,
        category=[],
        expected_pydash_version="8.0.6",
        worker_timeout=30,
    )

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="pydash worker timed out after 30 seconds",
    ):
        benchmark_pydash.run_worker_process("pydash", args, tmp_path / "missing.json")


def test_worker_process_bounds_failure_diagnostics(monkeypatch, tmp_path):
    def fail(command, **_kwargs):
        return subprocess.CompletedProcess(command, 7, "a" * 5000, "b" * 5000)

    monkeypatch.setattr(benchmark_pydash, "_run_bounded_process", fail)
    args = argparse.Namespace(
        iterations=1,
        repeats=1,
        category=[],
        expected_pydash_version="8.0.6",
        worker_timeout=30,
    )

    with pytest.raises(benchmark_pydash.PydashBenchmarkError) as caught:
        benchmark_pydash.run_worker_process("pydash", args, tmp_path / "missing.json")

    assert "pydash worker exited with code 7" in str(caught.value)
    assert "a" * benchmark_pydash.MAX_DIAGNOSTIC_CHARS in str(caught.value)
    assert "a" * (benchmark_pydash.MAX_DIAGNOSTIC_CHARS + 1) not in str(caught.value)
    assert "b" * benchmark_pydash.MAX_DIAGNOSTIC_CHARS in str(caught.value)
    assert "b" * (benchmark_pydash.MAX_DIAGNOSTIC_CHARS + 1) not in str(caught.value)


def test_bounded_process_capture_limits_memory_by_encoded_bytes():
    completed = benchmark_pydash._run_bounded_process(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stdout.buffer.write(b'a' * 5000); "
                "sys.stderr.buffer.write(b'b' * 5000); "
                "raise SystemExit(7)"
            ),
        ],
        timeout=30,
    )

    assert completed.returncode == 7
    assert completed.stdout.encode("utf-8") == b"a" * 4096
    assert completed.stderr.encode("utf-8") == b"b" * 4096


def test_bounded_process_capture_preserves_short_output():
    completed = benchmark_pydash._run_bounded_process(
        [sys.executable, "-c", "print('ok', end='')"],
        timeout=30,
    )

    assert completed.returncode == 0
    assert completed.stdout == "ok"
    assert completed.stderr == ""


def test_bounded_stream_reader_records_errors():
    class BrokenStream:
        def __init__(self):
            self.closed = False

        def read(self, _size):
            raise OSError("read failed")

        def close(self):
            self.closed = True

    stream = BrokenStream()
    errors = []

    benchmark_pydash._drain_bounded_stream(stream, bytearray(), errors) # type: ignore

    assert stream.closed
    assert len(errors) == 1
    assert isinstance(errors[0], OSError)


def test_bounded_process_rejects_start_failure(monkeypatch):
    def fail_start(*_args, **_kwargs):
        raise OSError("start failed")

    monkeypatch.setattr(benchmark_pydash.subprocess, "Popen", fail_start)

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="could not start worker process: OSError",
    ):
        benchmark_pydash._run_bounded_process([sys.executable], timeout=30)


def test_bounded_process_raises_timeout_after_killing_worker():
    with pytest.raises(subprocess.TimeoutExpired):
        benchmark_pydash._run_bounded_process(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout=0.01,
        )


def test_bounded_process_timeout_is_not_held_open_by_descendant_pipes():
    started = time.monotonic()
    child_code = (
        "import subprocess, sys, time; "
        "subprocess.Popen([sys.executable, '-c', "
        "'import time; time.sleep(2)']); "
        "time.sleep(2)"
    )

    with pytest.raises(subprocess.TimeoutExpired):
        benchmark_pydash._run_bounded_process(
            [sys.executable, "-c", child_code],
            timeout=0.05,
        )

    assert time.monotonic() - started < 1.0


def test_bounded_process_rejects_reader_failure(monkeypatch):
    def fail_reader(stream, _tail, errors):
        stream.close()
        errors.append(OSError("read failed"))

    monkeypatch.setattr(benchmark_pydash, "_drain_bounded_stream", fail_reader)

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="could not read worker diagnostics: OSError",
    ):
        benchmark_pydash._run_bounded_process(
            [sys.executable, "-c", "pass"],
            timeout=30,
        )


def test_process_tree_termination_uses_direct_kill_without_process_groups():
    process = SimpleNamespace(killed=False)

    def kill():
        process.killed = True

    process.kill = kill

    benchmark_pydash._terminate_process_tree(process, use_process_group=False) # type: ignore

    assert process.killed


def test_process_tree_termination_tolerates_missing_process_group(monkeypatch):
    def missing_group(_pid, _signal):
        raise ProcessLookupError

    monkeypatch.setattr(benchmark_pydash.os, "killpg", missing_group)

    benchmark_pydash._terminate_process_tree(
        SimpleNamespace(pid=123), # type: ignore
        use_process_group=True,
    )


def test_bounded_process_rejects_lingering_diagnostic_readers(monkeypatch):
    monkeypatch.setattr(benchmark_pydash, "_join_readers", lambda _readers: False)

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="worker diagnostic readers did not terminate",
    ):
        benchmark_pydash._run_bounded_process(
            [sys.executable, "-c", "pass"],
            timeout=30,
        )


def test_worker_process_rejects_missing_result(monkeypatch, tmp_path):
    monkeypatch.setattr(
        benchmark_pydash,
        "_run_bounded_process",
        lambda command, **_kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )
    args = argparse.Namespace(
        iterations=1,
        repeats=1,
        category=[],
        expected_pydash_version="8.0.6",
        worker_timeout=30,
    )

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="worker did not create result file",
    ):
        benchmark_pydash.run_worker_process("local", args, tmp_path / "missing.json")


def test_merge_reports_labels_ratio_direction():
    pydash_payload = _case_payload("pydash", seconds=4e-6, normalized=[1, 2]) # type: ignore
    local_payload = _case_payload("unicorefw", seconds=2e-6, normalized=[1, 2]) # type: ignore

    merged = _merge_reports(pydash_payload, local_payload)
    row = merged["cases"][0]

    assert row["speed_ratio"] == 2.0
    assert row["pydash"]["seconds"] == 4e-6
    assert row["unicorefw"]["seconds"] == 2e-6
    assert row["result_mismatch"] == ""
    assert merged["summary"] == {
        "selected_cases": 1,
        "benchmarked_both": 1,
        "missing_pydash": 0,
        "missing_unicorefw": 0,
        "failed_pydash": 0,
        "failed_unicorefw": 0,
        "skipped_pydash": 0,
        "skipped_unicorefw": 0,
        "result_mismatches": 0,
    }
    assert not benchmark_pydash.comparison_failed(merged, expected_cases=1)


def test_merge_reports_fails_closed_on_normalized_mismatch():
    pydash_payload = _case_payload("pydash", normalized=[1]) # type: ignore
    local_payload = _case_payload("unicorefw", normalized=[2]) # type: ignore

    merged = _merge_reports(pydash_payload, local_payload)

    assert merged["summary"]["result_mismatches"] == 1
    assert benchmark_pydash.comparison_failed(merged, expected_cases=1)


@pytest.mark.parametrize(
    ("pydash_status", "local_status", "summary_key"),
    [
        (
            benchmark_release.CaseStatus.MISSING,
            benchmark_release.CaseStatus.BENCHMARKED,
            "missing_pydash",
        ),
        (
            benchmark_release.CaseStatus.BENCHMARKED,
            benchmark_release.CaseStatus.MISSING,
            "missing_unicorefw",
        ),
        (
            benchmark_release.CaseStatus.FAILED,
            benchmark_release.CaseStatus.BENCHMARKED,
            "failed_pydash",
        ),
        (
            benchmark_release.CaseStatus.BENCHMARKED,
            benchmark_release.CaseStatus.FAILED,
            "failed_unicorefw",
        ),
        (
            benchmark_release.CaseStatus.SKIPPED,
            benchmark_release.CaseStatus.BENCHMARKED,
            "skipped_pydash",
        ),
        (
            benchmark_release.CaseStatus.BENCHMARKED,
            benchmark_release.CaseStatus.SKIPPED,
            "skipped_unicorefw",
        ),
    ],
)
def test_merge_reports_counts_each_non_benchmark_status(
    pydash_status, local_status, summary_key
):
    pydash_payload = _case_payload(
        "pydash",
        status=pydash_status,
        seconds=(
            1e-6 if pydash_status == benchmark_release.CaseStatus.BENCHMARKED else None
        ), # type: ignore
    )
    local_payload = _case_payload(
        "unicorefw",
        status=local_status,
        seconds=(
            1e-6 if local_status == benchmark_release.CaseStatus.BENCHMARKED else None
        ), # type: ignore
    )
    if pydash_status == benchmark_release.CaseStatus.MISSING:
        pydash_payload = replace(pydash_payload, api_names=frozenset())
        pydash_payload.report.api_count = 0
    if local_status == benchmark_release.CaseStatus.MISSING:
        local_payload = replace(local_payload, api_names=frozenset())
        local_payload.report.api_count = 0

    merged = _merge_reports(pydash_payload, local_payload)

    assert merged["summary"][summary_key] == 1
    assert benchmark_pydash.comparison_failed(merged, expected_cases=1)


def test_comparison_fails_on_incomplete_selected_accounting():
    merged = _merge_reports(
        _case_payload("pydash"),
        _case_payload("unicorefw"),
    )

    assert benchmark_pydash.comparison_failed(merged, expected_cases=2)


def test_merge_reports_rejects_mismatched_case_sets():
    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="worker case sets differ",
    ):
        _merge_reports(
            _case_payload("pydash", name="identity"),
            _case_payload("unicorefw", name="noop"),
        )


def test_merge_reports_rejects_same_wrong_selected_case_set():
    expected_keys = frozenset({("utility", "identity")})

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="worker case set differs from selected benchmark cases",
    ):
        benchmark_pydash.merge_reports(
            _case_payload("pydash", name="noop"),
            _case_payload("unicorefw", name="noop"),
            expected_keys,
        )


def test_merge_reports_rejects_duplicate_cases():
    pydash_payload = _case_payload("pydash")
    pydash_payload.report.results.append(pydash_payload.report.results[0])

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="pydash worker reported duplicate cases",
    ):
        _merge_reports(
            pydash_payload,
            _case_payload("unicorefw"),
        )


def test_merge_reports_rejects_wrong_worker_labels():
    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="unexpected worker implementation labels",
    ):
        _merge_reports(
            _case_payload("unicorefw"),
            _case_payload("pydash"),
        )


def test_merge_reports_rejects_inconsistent_expected_versions():
    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="worker expected versions differ",
    ):
        _merge_reports(
            _case_payload("pydash"),
            _case_payload("unicorefw", expected_version="9.0.0"),
        )


@pytest.mark.parametrize(
    ("pydash_seconds", "local_seconds", "expected"),
    [
        (4e-6, 2e-6, "UniCoreFW 2.00x faster"),
        (2e-6, 4e-6, "pydash 2.00x faster"),
        (2e-6, 2e-6, "equal"),
    ],
)
def test_text_report_describes_ratio_direction(pydash_seconds, local_seconds, expected):
    merged = _merge_reports(
        _case_payload("pydash", seconds=pydash_seconds),
        _case_payload("unicorefw", seconds=local_seconds),
    )

    report = benchmark_pydash.render_text_report(merged, verbose=True)

    assert expected in report
    assert "Pydash 8.0.6" in report
    assert "UniCoreFW 1.1.5" in report
    assert "Release" not in report
    assert "local_api_count: 1" in report
    assert "pydash_api_count: 1" in report


def test_text_report_displays_failure_detail():
    merged = _merge_reports(
        _case_payload(
            "pydash",
            status=benchmark_release.CaseStatus.FAILED,
            seconds=None, # type: ignore
            detail="TypeError: fixed fixture failed",
        ),
        _case_payload("unicorefw"),
    )

    report = benchmark_pydash.render_text_report(merged)

    assert "pydash FAILED: TypeError: fixed fixture failed" in report


def test_text_report_handles_zero_timing_ratio():
    merged = _merge_reports(
        _case_payload("pydash", seconds=0.0),
        _case_payload("unicorefw", seconds=1e-6),
    )

    assert "timing ratio unavailable" in benchmark_pydash.render_text_report(merged)


def test_text_report_lists_incompatible_reason():
    merged = _merge_reports(
        _case_payload("pydash"),
        _case_payload("unicorefw"),
    )
    merged["inventory"]["incompatible_shared"] = {
        "flatten": "normalized result differs from UniCoreFW"
    }

    assert (
        "flatten: normalized result differs from UniCoreFW"
        in benchmark_pydash.render_text_report(merged, verbose=True)
    )


def test_json_report_replaces_destination_after_fsync(monkeypatch, tmp_path):
    destination = tmp_path / "report.json"
    events = []
    real_fsync = os.fsync
    real_replace = os.replace

    def fsync(fd):
        events.append("fsync")
        return real_fsync(fd)

    def replace(source, target):
        events.append("replace")
        assert Path(source).parent == destination.parent
        assert Path(target) == destination
        return real_replace(source, target)

    monkeypatch.setattr(benchmark_pydash.os, "fsync", fsync)
    monkeypatch.setattr(benchmark_pydash.os, "replace", replace)

    benchmark_pydash.write_json_report({"z": 1, "a": 2}, destination)

    assert events == ["fsync", "replace"]
    assert destination.read_text(encoding="utf-8").index('"a"') < (
        destination.read_text(encoding="utf-8").index('"z"')
    )
    assert json.loads(destination.read_text(encoding="utf-8")) == {"a": 2, "z": 1}


def test_json_report_preserves_destination_on_serialization_failure(tmp_path):
    destination = tmp_path / "report.json"
    destination.write_text("original", encoding="utf-8")

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="could not write JSON report",
    ):
        benchmark_pydash.write_json_report({"invalid": {1}}, destination)

    assert destination.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.iterdir()) == [destination]


def test_json_report_cleans_temporary_file_after_replace_failure(monkeypatch, tmp_path):
    destination = tmp_path / "report.json"
    destination.write_text("original", encoding="utf-8")

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr(benchmark_pydash.os, "replace", fail_replace)

    with pytest.raises(
        benchmark_pydash.PydashBenchmarkError,
        match="could not write JSON report",
    ):
        benchmark_pydash.write_json_report({"valid": True}, destination)

    assert destination.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.iterdir()) == [destination]


def test_json_report_tolerates_missing_temporary_file_during_cleanup(
    monkeypatch, tmp_path
):
    destination = tmp_path / "report.json"

    def remove_then_fail(source, _target):
        Path(source).unlink()
        raise OSError("replace failed")

    monkeypatch.setattr(benchmark_pydash.os, "replace", remove_then_fail)

    with pytest.raises(benchmark_pydash.PydashBenchmarkError):
        benchmark_pydash.write_json_report({"valid": True}, destination)

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("name", "value", "maximum"),
    [
        ("iterations", "0", benchmark_pydash.MAX_ITERATIONS),
        (
            "iterations",
            str(benchmark_pydash.MAX_ITERATIONS + 1),
            benchmark_pydash.MAX_ITERATIONS,
        ),
        ("repeats", "0", benchmark_pydash.MAX_REPEATS),
        (
            "repeats",
            str(benchmark_pydash.MAX_REPEATS + 1),
            benchmark_pydash.MAX_REPEATS,
        ),
        ("worker timeout", "0", benchmark_pydash.MAX_WORKER_TIMEOUT),
        (
            "worker timeout",
            str(benchmark_pydash.MAX_WORKER_TIMEOUT + 1),
            benchmark_pydash.MAX_WORKER_TIMEOUT,
        ),
        ("iterations", "not-an-integer", benchmark_pydash.MAX_ITERATIONS),
    ],
)
def test_bounded_integer_rejects_invalid_values(name, value, maximum):
    validator = benchmark_pydash._bounded_integer(name, maximum)

    with pytest.raises(argparse.ArgumentTypeError):
        validator(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", 1),
        (str(benchmark_pydash.MAX_ITERATIONS), benchmark_pydash.MAX_ITERATIONS),
    ],
)
def test_bounded_integer_accepts_inclusive_boundaries(value, expected):
    validator = benchmark_pydash._bounded_integer(
        "iterations", benchmark_pydash.MAX_ITERATIONS
    )

    assert validator(value) == expected


def test_bounded_integer_rejects_boolean():
    validator = benchmark_pydash._bounded_integer(
        "iterations", benchmark_pydash.MAX_ITERATIONS
    )

    with pytest.raises(argparse.ArgumentTypeError):
        validator(True)


@pytest.mark.parametrize("value", ["", " " * 2, "8.0.6\n", "8.0.6\x01", "x" * 129])
def test_expected_version_rejects_unsafe_values(value):
    with pytest.raises(argparse.ArgumentTypeError):
        benchmark_pydash._expected_version(value)


def test_parser_uses_bounded_reproducible_defaults():
    args = benchmark_pydash.build_parser().parse_args([])

    assert args.iterations == benchmark_pydash.DEFAULT_ITERATIONS
    assert args.repeats == benchmark_pydash.DEFAULT_REPEATS
    assert args.worker_timeout == benchmark_pydash.DEFAULT_WORKER_TIMEOUT
    assert args.expected_pydash_version == "8.0.6"
    assert args.category == []
    assert args.worker is None


def test_parser_accepts_repeated_categories_and_version_override():
    args = benchmark_pydash.build_parser().parse_args(
        [
            "--category",
            "array",
            "--category",
            "type",
            "--expected-pydash-version",
            "9.0.0",
        ]
    )

    assert args.category == ["array", "type"]
    assert args.expected_pydash_version == "9.0.0"


def test_list_mode_does_not_import_benchmark_targets(monkeypatch, capsys):
    def reject_import(*_args, **_kwargs):
        raise AssertionError("list mode imported a benchmark target")

    monkeypatch.setattr(benchmark_pydash, "import_target", reject_import)

    assert benchmark_pydash.main(["--list", "--category", "type"]) == 0

    lines = capsys.readouterr().out.splitlines()
    assert lines
    assert all(line.split("\t")[1] == "type" for line in lines)
    assert all(
        line.split("\t")[0] in benchmark_pydash.COMPARABLE_CASE_NAMES for line in lines
    )


def test_worker_mode_requires_result_file():
    with pytest.raises(SystemExit) as caught:
        benchmark_pydash.main(["--worker", "local"])

    assert caught.value.code == 2


def test_parent_mode_prints_valid_comparison(monkeypatch, capsys):
    payloads = {
        "pydash": _case_payload("pydash"),
        "local": _case_payload("unicorefw"),
    }
    monkeypatch.setattr(
        benchmark_pydash,
        "run_worker_process",
        lambda mode, _args, _path: payloads[mode],
    )
    monkeypatch.setattr(
        benchmark_pydash,
        "build_comparable_cases",
        lambda _categories=None: [SimpleNamespace(name="identity", category="utility")],
    )

    assert benchmark_pydash.main(["--verbose"]) == 0

    output = capsys.readouterr().out
    assert "Pydash 8.0.6" in output
    assert "UniCoreFW 1.1.5" in output
    assert "result_mismatches: 0" in output


def test_parent_mode_writes_json_only_for_valid_comparison(monkeypatch, tmp_path):
    destination = tmp_path / "report.json"
    payloads = {
        "pydash": _case_payload("pydash"),
        "local": _case_payload("unicorefw"),
    }
    monkeypatch.setattr(
        benchmark_pydash,
        "run_worker_process",
        lambda mode, _args, _path: payloads[mode],
    )
    monkeypatch.setattr(
        benchmark_pydash,
        "build_comparable_cases",
        lambda _categories=None: [SimpleNamespace(name="identity", category="utility")],
    )

    assert benchmark_pydash.main(["--json", str(destination)]) == 0
    assert (
        json.loads(destination.read_text(encoding="utf-8"))["summary"][
            "benchmarked_both"
        ]
        == 1
    )

    payloads["local"] = _case_payload("unicorefw", normalized="different")
    destination.unlink()

    assert benchmark_pydash.main(["--json", str(destination)]) == 1
    assert not destination.exists()


def test_parent_mode_reports_bounded_operational_error(monkeypatch, capsys):
    def fail(*_args, **_kwargs):
        raise benchmark_pydash.PydashBenchmarkError("worker failed")

    monkeypatch.setattr(benchmark_pydash, "run_worker_process", fail)

    assert benchmark_pydash.main([]) == 1
    assert capsys.readouterr().err == "pydash benchmark failed: worker failed\n"


def test_hidden_worker_mode_writes_payload(monkeypatch, tmp_path, capsys):
    destination = tmp_path / "worker.json"
    payload = _worker_payload()
    monkeypatch.setattr(
        benchmark_pydash,
        "run_worker",
        lambda *_args, **_kwargs: payload,
    )

    assert (
        benchmark_pydash.main(
            [
                "--worker",
                "pydash",
                "--result-file",
                str(destination),
                "--iterations",
                "1",
                "--repeats",
                "1",
            ]
        )
        == 0
    )
    assert benchmark_pydash.read_worker_payload(destination) == payload
    assert capsys.readouterr().out == ""


def test_script_direct_entry_point(monkeypatch, capsys):
    script_path = Path(benchmark_pydash.__file__).resolve()
    monkeypatch.syspath_prepend(str(benchmark_pydash.SCRIPTS_ROOT))
    monkeypatch.setattr(
        sys,
        "argv",
        [str(script_path), "--list", "--category", "type"],
    )

    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(script_path), run_name="__main__")

    assert caught.value.code == 0
    assert capsys.readouterr().out


def test_ci_installs_pinned_benchmark_dependency():
    workflow = (
        benchmark_pydash.PROJECT_ROOT / ".github/workflows/tests.yml"
    ).read_text(encoding="utf-8")

    assert workflow.count("\"pydash==8.0.6; python_version >= '3.9'\"") == 2


def test_script_compares_installed_pydash_with_local_unicorefw():
    _require_baseline_pydash()
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/benchmark_pydash.py",
            "--iterations",
            "1",
            "--repeats",
            "1",
                "--category",
                "type",
                "--verbose",
            ],
        cwd=benchmark_pydash.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Pydash 8.0.6" in completed.stdout
    assert "UniCoreFW" in completed.stdout
    assert "result_mismatches: 0" in completed.stdout
