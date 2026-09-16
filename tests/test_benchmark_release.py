"""Regression tests for the release benchmark registry."""


from __future__ import annotations

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from scripts import benchmark_release
from unicorefw import UniCoreFW

sys.dont_write_bytecode = True

NEW_CASE_NAMES = frozenset(
    {
        "html_template",
        "require_callable",
        "unsafe_raw_css",
        "unsafe_raw_sql",
    }
)


def _new_cases():
    return [
        case
        for case in benchmark_release.build_all_cases()
        if case.name in NEW_CASE_NAMES
    ]


def test_release_benchmark_registry_covers_each_local_callable_once():
    audit = benchmark_release.audit_cases(
        benchmark_release.discover_public_api_names(UniCoreFW), # type: ignore
        benchmark_release.build_all_cases(),
    )

    assert audit == benchmark_release.CoverageAudit((), (), ())


def test_new_release_benchmark_cases_execute_and_redact_trusted_fragments():
    cases = {case.name: case for case in _new_cases()}

    assert set(cases) == NEW_CASE_NAMES
    results = {
        name: benchmark_release.run_case(
            UniCoreFW,
            case,
            iterations=1,
            repeats=1,
            warmups=0,
        )
        for name, case in cases.items()
    }

    assert all(
        result.status == benchmark_release.CaseStatus.BENCHMARKED
        for result in results.values()
    )
    assert results["require_callable"].normalized is None
    assert results["html_template"].normalized == ("<p>&lt;Alice &amp; Bob&gt;</p>")
    assert results["unsafe_raw_sql"].normalized == {"type": "UnsafeSQL"}
    assert results["unsafe_raw_css"].normalized == {"type": "UnsafeCSS"}
    assert "COUNT(*)" not in repr(results["unsafe_raw_sql"].normalized)
    assert "color: red" not in repr(results["unsafe_raw_css"].normalized)


def test_new_cases_report_missing_for_an_older_release_api():
    results = [
        benchmark_release.run_case(
            SimpleNamespace(),
            case,
            iterations=1,
            repeats=1,
            warmups=0,
        )
        for case in _new_cases()
    ]

    assert len(results) == 4
    assert all(
        result.status == benchmark_release.CaseStatus.MISSING for result in results
    )
    assert all(
        result.detail == "implementation does not expose " + result.name
        for result in results
    )


def test_release_registry_filters_one_api():
    selected = benchmark_release._selected_registry(frozenset(), "identity") # type: ignore

    assert [(case.category, case.name) for case in selected] == [
        ("utility", "identity")
    ]
