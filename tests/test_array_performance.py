"""Compatibility and complexity tests for optimized collection operations."""

from __future__ import annotations

import importlib
import math
import os
import sys
from typing import Any

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from scripts import benchmark_collections

array_module = importlib.import_module("unicorefw.array")


class _UnhashableAlias:
    __hash__ = None # type: ignore

    def __init__(self, value: int) -> None:
        self.value = value

    def __eq__(self, other: Any) -> bool:  # noqa: PYI032
        if isinstance(other, _UnhashableAlias):
            return self.value == other.value
        return self.value == other


class _HashProbe:
    equality_calls = 0
    hash_calls = 0

    def __init__(self, value: int) -> None:
        self.value = value

    def __eq__(self, other: Any) -> bool:  # noqa: PYI032
        type(self).equality_calls += 1
        return isinstance(other, _HashProbe) and self.value == other.value

    def __hash__(self) -> int:
        type(self).hash_calls += 1
        return hash(self.value)

    @classmethod
    def reset(cls) -> None:
        cls.equality_calls = 0
        cls.hash_calls = 0


class _GroupValue:
    def __init__(self, value: str, group: int) -> None:
        self.value = value
        self.group = group


def _probe_values(values):
    return [_HashProbe(value) for value in values]


def test_stable_uniqueness_preserves_order_and_cross_hash_equality():
    first_alias = _UnhashableAlias(1)
    second_alias = _UnhashableAlias(2)

    result = array_module.uniq([1, first_alias, second_alias, 2])

    assert result == [1, second_alias]
    assert result[1] is second_alias
    assert array_module.uniq([first_alias, 1]) == [first_alias]
    assert array_module.union([first_alias], [1, second_alias, 2]) == [
        first_alias,
        second_alias,
    ]


def test_stable_uniqueness_retains_python_nan_identity_semantics():
    first_nan = math.nan
    second_nan = float("nan")

    result = array_module.uniq([first_nan, first_nan, second_nan])

    assert len(result) == 2
    assert result[0] is first_nan
    assert result[1] is second_nan


def test_equality_based_operations_support_unhashable_values():
    assert array_module.difference([[1], [2], [1]], [[2]]) == [[1], [1]]
    assert array_module.without([[1], [2], [1]], [2]) == [[1], [1]]
    assert array_module.pull([[1], [2], [1]], [2]) == [[1], [1]]
    assert array_module.pull_all([[1], [2], [1]], [[2]]) == [[1], [1]]
    assert array_module.pull_all_with([[1], [2], [1]], [[2]]) == [
        [1],
        [1],
    ]
    assert array_module.pull_all_by([[1], [2]], [[2]]) == [[1]]
    assert array_module.union([[1], [1]], [[2]]) == [[1], [2]]
    assert array_module.intersection([[1], [1], [2]], [[1]]) == [[1]]
    assert array_module.xor([[1], [1]], [[2]]) == [[1], [2]]
    assert array_module.sorted_uniq([[2], [1], [1]]) == [[1], [2]]


def test_keyed_operations_support_unhashable_derived_keys():
    parity_key = lambda value: [value % 2]

    assert array_module.uniq_by([1, 3, 2, 4], parity_key) == [1, 2]
    assert array_module.union_by(
        [1, 3],
        [2, 4],
        iteratee=parity_key,
    ) == [1, 2]
    assert array_module.difference_by([1, 2], [3], parity_key) == [2]
    assert array_module.intersection_by([1, 2], [3], parity_key) == [1]
    assert array_module.xor_by([1, 2], [3], parity_key) == [2]
    assert array_module.pull_all_by([1, 2], [3], parity_key) == [2]
    assert array_module.duplicates([1, 3, 2, 4, 5], parity_key) == [3, 4]
    assert array_module.sorted_uniq_by([3, 1, 2, 4], parity_key) == [2, 3]


def test_optimized_keyed_operations_cover_empty_and_attribute_paths():
    first = _GroupValue("first", 1)
    duplicate = _GroupValue("duplicate", 1)
    other = _GroupValue("other", 2)

    assert array_module.union_by() == []
    assert array_module.union_by(iteratee=lambda value: value) == []
    assert array_module.intersection_by(
        [first, duplicate, other],
        [_GroupValue("match", 1)],
        "group",
    ) == [first]
    assert array_module.sorted_uniq_by([], lambda value: value) == []


def test_sorted_uniq_by_rejects_invalid_or_failing_iteratees():
    with pytest.raises(TypeError, match="Iteratee must be callable"):
        array_module.sorted_uniq_by([1], None)

    with pytest.raises(TypeError, match="Iteratee function failed"):
        array_module.sorted_uniq_by(
            [1],
            lambda value: value.missing,
        )


def test_xor_coalesces_duplicate_contributors_as_documented():
    assert array_module.xor() == []
    assert array_module.xor([1, 1], [2, 2]) == [1, 2]
    assert array_module.xor([1, 1]) == [1]
    assert array_module.xor_by(lambda value: value) == []
    assert array_module.xor_by([1, 1], [2, 2], lambda value: value) == [1, 2]
    with pytest.raises(TypeError, match="Missing iteratee"):
        array_module.xor_by([1, 2])


def test_difference_with_default_equality_remains_pairwise():
    assert array_module.difference_with([[1], [2]], [[2]]) == [[1]]


def test_union_retains_legacy_iteratee_keyword_behavior():
    assert array_module.union(
        [1, 3],
        [2, 4],
        iteratee=lambda value: value % 2,
    ) == [1, 3, 2, 4]


@pytest.mark.parametrize(
    ("operation", "expected_values", "input_count"),
    [
        (
            lambda left, right: array_module.uniq(left),
            list(range(512)),
            512,
        ),
        (
            lambda left, right: array_module.union(left, right),
            list(range(768)),
            1024,
        ),
        (
            lambda left, right: array_module.difference(left, right),
            list(range(256)),
            1024,
        ),
        (
            lambda left, right: array_module.intersection(left, right),
            list(range(256, 512)),
            1024,
        ),
        (
            lambda left, right: array_module.xor(left, right),
            list(range(256)) + list(range(512, 768)),
            1024,
        ),
    ],
)
def test_hashable_collection_paths_have_linear_operation_counts(
    operation,
    expected_values,
    input_count,
):
    left = _probe_values(range(512))
    right = _probe_values(range(256, 768))
    _HashProbe.reset()

    result = operation(left, right)

    assert [item.value for item in result] == expected_values
    assert _HashProbe.hash_calls <= input_count * 10
    assert _HashProbe.equality_calls <= input_count * 2


def test_take_right_while_preserves_predicate_order_without_front_inserts():
    values = [1, 2, 3, 4]
    visited = []

    result = array_module.take_right_while(
        values,
        lambda value: visited.append(value) is None and value >= 3,
    )

    assert result == [3, 4]
    assert result is not values
    assert values == [1, 2, 3, 4]
    assert visited == [4, 3, 2]


def test_unshift_performs_one_stable_in_place_prefix_update():
    values = [3, 4]

    result = array_module.unshift(values, 1, 2)

    assert result is values
    assert values == [1, 2, 3, 4]
    assert array_module.unshift(values) is values


def test_collection_benchmark_runs_selected_bounded_scenarios():
    summaries = benchmark_collections.benchmark_collections(
        runs=1,
        size=8,
        scenarios=["uniq_all_unique", "uniq_unhashable"],
    )

    assert [summary["scenario"] for summary in summaries] == [
        "uniq_all_unique",
        "uniq_unhashable",
    ]
    assert all(summary["runs"] == 1 for summary in summaries)
    assert all(summary["median_ms"] >= 0 for summary in summaries)


def test_collection_benchmark_default_selection_covers_every_scenario():
    summaries = benchmark_collections.benchmark_collections(runs=1, size=8)

    assert [summary["scenario"] for summary in summaries] == list(
        benchmark_collections.SCENARIOS
    )
    assert all(summary["maximum_ms"] >= summary["median_ms"] for summary in summaries)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"runs": True},
        {"runs": 0},
        {"runs": benchmark_collections.MAX_RUNS + 1},
        {"size": True},
        {"size": 0},
        {"size": benchmark_collections.MAX_SIZE + 1},
        {"scenarios": ["missing"]},
        {"scenarios": ["uniq_all_unique", "uniq_all_unique"]},
    ],
)
def test_collection_benchmark_rejects_invalid_budgets(kwargs):
    with pytest.raises(benchmark_collections.CollectionBenchmarkError):
        benchmark_collections.benchmark_collections(**kwargs)


def test_collection_benchmark_fails_closed_on_wrong_result(monkeypatch):
    monkeypatch.setitem(
        benchmark_collections.SCENARIOS,
        "invalid_result",
        lambda size: (size, [], lambda result: False),
    )

    with pytest.raises(
        benchmark_collections.CollectionBenchmarkError,
        match="unexpected result",
    ):
        benchmark_collections.benchmark_collections(
            runs=1,
            size=1,
            scenarios=["invalid_result"],
        )


def test_collection_benchmark_cli_emits_json(capsys):
    assert (
        benchmark_collections.main(
            [
                "--runs",
                "1",
                "--size",
                "8",
                "--scenario",
                "uniq_all_unique",
            ]
        )
        == 0
    )

    assert '"scenario": "uniq_all_unique"' in capsys.readouterr().out


def test_collection_benchmark_cli_reports_fail_closed_errors(
    monkeypatch,
    capsys,
):
    def fail_benchmark(**kwargs):
        raise benchmark_collections.CollectionBenchmarkError("fixture failure")

    monkeypatch.setattr(
        benchmark_collections,
        "benchmark_collections",
        fail_benchmark,
    )

    assert benchmark_collections.main([]) == 1
    assert "fixture failure" in capsys.readouterr().err
