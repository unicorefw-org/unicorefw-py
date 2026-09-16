"""Tests for bounded UniCoreFW dispatch benchmarks."""

from __future__ import annotations

import importlib
import os
import runpy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from scripts import benchmark_dispatch


def test_dispatch_benchmark_reports_all_required_scenarios():
    module = importlib.import_module("scripts.benchmark_dispatch")

    summaries = module.benchmark_dispatch(runs=1, iterations=2)

    assert [item["scenario"] for item in summaries] == [
        "direct",
        "static",
        "factory_static",
        "five_step_chain",
    ]
    assert all(item["runs"] == 1 for item in summaries)
    assert all(item["iterations"] == 2 for item in summaries)
    assert all(item["median_ns_per_call"] >= 0 for item in summaries)


def test_dispatch_benchmark_runs_selected_scenarios_in_requested_order():
    summaries = benchmark_dispatch.benchmark_dispatch(
        runs=1,
        iterations=1,
        scenarios=["five_step_chain", "direct"],
    )

    assert [item["scenario"] for item in summaries] == [
        "five_step_chain",
        "direct",
    ]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"runs": True},
        {"runs": 0},
        {"runs": 26},
        {"iterations": True},
        {"iterations": 0},
        {"iterations": 1_000_001},
        {"scenarios": []},
        {"scenarios": ["missing"]},
        {"scenarios": ["direct", "direct"]},
        {"maximum_median_ns": True},
        {"maximum_median_ns": -1},
        {"maximum_median_ns": float("nan")},
        {"maximum_median_ns": float("inf")},
    ],
)
def test_dispatch_benchmark_rejects_invalid_configuration(kwargs):
    options = {"runs": 1, "iterations": 1, "scenarios": ["direct"]}
    options.update(kwargs)

    with pytest.raises(benchmark_dispatch.DispatchBenchmarkError):
        benchmark_dispatch.benchmark_dispatch(**options)


def test_dispatch_benchmark_fails_closed_on_wrong_result(monkeypatch):
    monkeypatch.setitem(
        benchmark_dispatch.SCENARIOS,
        "invalid_result",
        (lambda: "wrong", "expected"),
    )

    with pytest.raises(
        benchmark_dispatch.DispatchBenchmarkError,
        match="invalid_result returned an unexpected result",
    ):
        benchmark_dispatch.benchmark_dispatch(
            runs=1,
            iterations=1,
            scenarios=["invalid_result"],
        )


def test_dispatch_benchmark_enforces_median_budget():
    with pytest.raises(
        benchmark_dispatch.DispatchBenchmarkError,
        match="direct median",
    ):
        benchmark_dispatch.benchmark_dispatch(
            runs=1,
            iterations=1,
            scenarios=["direct"],
            maximum_median_ns=0,
        )


def test_dispatch_benchmark_cli_emits_json(capsys):
    assert (
        benchmark_dispatch.main(
            [
                "--runs",
                "1",
                "--iterations",
                "2",
                "--scenario",
                "direct",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert '"scenario": "direct"' in output
    assert '"iterations": 2' in output


def test_dispatch_benchmark_cli_reports_redacted_errors(monkeypatch, capsys):
    def fail_benchmark(**kwargs):
        raise benchmark_dispatch.DispatchBenchmarkError("fixture failure")

    monkeypatch.setattr(
        benchmark_dispatch,
        "benchmark_dispatch",
        fail_benchmark,
    )

    assert benchmark_dispatch.main([]) == 1
    assert capsys.readouterr().err == "dispatch benchmark failed: fixture failure\n"


def test_dispatch_benchmark_script_entry_point(monkeypatch, capsys):
    script_path = Path(benchmark_dispatch.__file__).resolve()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(script_path),
            "--runs",
            "1",
            "--iterations",
            "1",
            "--scenario",
            "direct",
        ],
    )

    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(script_path), run_name="__main__")

    assert caught.value.code == 0
    assert '"scenario": "direct"' in capsys.readouterr().out
