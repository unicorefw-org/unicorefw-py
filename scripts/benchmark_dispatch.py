"""Benchmark representative UniCoreFW dispatch paths."""

from __future__ import annotations

import argparse
import gc
import importlib
import json
import math
import statistics
import sys
import time
from collections.abc import Sequence
from numbers import Real
from pathlib import Path
from typing import Any, Callable, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from unicorefw import UniCoreFW, _

utils_module = importlib.import_module("unicorefw.utils")

DEFAULT_ITERATIONS = 100_000
DEFAULT_RUNS = 7
MAX_ITERATIONS = 1_000_000
MAX_RUNS = 25
_VALUE = "dispatch"

Operation = Callable[[], Any]
Scenario = Tuple[Operation, Any]


class DispatchBenchmarkError(ValueError):
    """Raised when a dispatch benchmark cannot run safely."""


def _direct_call() -> str:
    return utils_module.identity(_VALUE)


def _static_call() -> str:
    return UniCoreFW.identity(_VALUE)


def _factory_static_call() -> str:
    return _.identity(_VALUE)


def _five_step_chain() -> str:
    return _(_VALUE).identity().identity().identity().identity().identity().value() # type: ignore


SCENARIOS: dict[str, Scenario] = {
    "direct": (_direct_call, _VALUE),
    "static": (_static_call, _VALUE),
    "factory_static": (_factory_static_call, _VALUE),
    "five_step_chain": (_five_step_chain, _VALUE),
}


def _validate_bounded_integer(name: str, value: int, maximum: int) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= maximum
    ):
        raise DispatchBenchmarkError(
            f"{name} must be an integer between 1 and {maximum}"
        )


def _validate_maximum_median_ns(value: float | None) -> None:
    if value is None:
        return
    if (
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not math.isfinite(value)
        or value < 0
    ):
        raise DispatchBenchmarkError(
            "maximum_median_ns must be a finite non-negative number"
        )


def benchmark_dispatch(
    *,
    runs: int = DEFAULT_RUNS,
    iterations: int = DEFAULT_ITERATIONS,
    scenarios: Sequence[str] | None = None,
    maximum_median_ns: float | None = None,
) -> list[dict[str, Any]]:
    """Return timing summaries for representative dispatch paths."""
    _validate_bounded_integer("runs", runs, MAX_RUNS)
    _validate_bounded_integer("iterations", iterations, MAX_ITERATIONS)
    _validate_maximum_median_ns(maximum_median_ns)

    selected = list(SCENARIOS) if scenarios is None else list(scenarios)
    if not selected:
        raise DispatchBenchmarkError("scenarios must not be empty")
    unknown = sorted(set(selected) - set(SCENARIOS))
    if unknown:
        raise DispatchBenchmarkError(f"unknown scenarios: {', '.join(unknown)}")
    if len(selected) != len(set(selected)):
        raise DispatchBenchmarkError("scenarios must not contain duplicates")

    summaries = []
    for name in selected:
        operation, expected = SCENARIOS[name]
        durations = []
        for _run_index in range(runs):
            gc.collect()
            started = time.perf_counter_ns()
            result = None
            for _iteration_index in range(iterations):
                result = operation()
            elapsed_ns = time.perf_counter_ns() - started
            if result != expected:
                raise DispatchBenchmarkError(f"{name} returned an unexpected result")
            durations.append(elapsed_ns / iterations)
        median_ns_per_call = statistics.median(durations)
        if maximum_median_ns is not None and median_ns_per_call > maximum_median_ns:
            raise DispatchBenchmarkError(
                f"{name} median {median_ns_per_call:.3f} ns per call exceeds "
                f"{maximum_median_ns:.3f} ns"
            )
        summaries.append(
            {
                "iterations": iterations,
                "maximum_ns_per_call": max(durations),
                "median_ns_per_call": median_ns_per_call,
                "runs": runs,
                "scenario": name,
            }
        )
    return summaries


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
    )
    parser.add_argument(
        "--scenario",
        action="append",
        choices=tuple(SCENARIOS),
        dest="scenarios",
    )
    parser.add_argument("--max-median-ns", type=float)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        summaries = benchmark_dispatch(
            runs=args.runs,
            iterations=args.iterations,
            scenarios=args.scenarios,
            maximum_median_ns=args.max_median_ns,
        )
    except DispatchBenchmarkError as exc:
        print(f"dispatch benchmark failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summaries, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
