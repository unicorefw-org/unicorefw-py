"""Measure isolated UniCoreFW imports and enforce the root import budget."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import statistics
import subprocess
import sys
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

OPTIONAL_MODULE_PREFIXES = (
    "cryptography",
    "openpyxl",
    "pandas",
    "psycopg2",
    "pymongo",
    "pymysql",
    "redis",
    "sqlalchemy",
)
MAX_RUNS = 50
MAX_WORKER_OUTPUT_BYTES = 64 * 1024
WORKER_TIMEOUT_SECONDS = 30


class ImportBudgetError(RuntimeError):
    """Raised when an import violates a performance or isolation contract."""


def _rss_kib() -> int:
    """Return current resident memory on Linux, or a safe portable fallback."""
    statm_path = Path("/proc/self/statm")
    try:
        resident_pages = int(
            statm_path.read_text(encoding="ascii").split()[1]
        )
        return resident_pages * os.sysconf("SC_PAGE_SIZE") // 1024 # type: ignore
    except (IndexError, OSError, TypeError, ValueError):
        try:
            import resource

            maximum_rss = int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss # type: ignore
            )
        except (ImportError, ValueError):
            return 0
        if sys.platform == "darwin":
            return maximum_rss // 1024
        return maximum_rss


def _is_write_open(arguments: Any) -> bool:
    try:
        mode = arguments[1]
        flags = arguments[2]
    except (IndexError, TypeError):
        return False
    if isinstance(mode, str) and any(marker in mode for marker in "wax+"):
        return True
    write_flags = (
        os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
    )
    return isinstance(flags, int) and bool(flags & write_flags)


def _worker_result(target: str) -> dict[str, Any]:
    side_effect_events: list[str] = []

    def audit_hook(event: str, arguments: Any) -> None:
        if event == "open" and _is_write_open(arguments):
            side_effect_events.append("file-write")
        elif event in {
            "os.system",
            "socket.connect",
            "sqlite3.connect",
            "subprocess.Popen",
        }:
            side_effect_events.append(event)

    add_audit_hook = getattr(sys, "addaudithook", None)
    if add_audit_hook is not None:
        add_audit_hook(audit_hook)
    import logging

    original_thread_start = threading.Thread.start
    original_add_handler = logging.Logger.addHandler
    original_handle = logging.Logger.handle

    def audited_thread_start(thread: threading.Thread, *args: Any, **kwargs: Any):
        side_effect_events.append("thread-start")
        return original_thread_start(thread, *args, **kwargs)

    def audited_add_handler(
        logger: logging.Logger,
        handler: logging.Handler,
    ) -> None:
        side_effect_events.append("logging-handler")
        original_add_handler(logger, handler)

    def audited_log_handle(
        logger: logging.Logger,
        record: logging.LogRecord,
    ) -> None:
        side_effect_events.append("logging-record")
        original_handle(logger, record)

    threads_before = threading.active_count()
    handlers_before = tuple(logging.getLogger().handlers)
    rss_before = _rss_kib()
    threading.Thread.start = audited_thread_start # type: ignore
    logging.Logger.addHandler = audited_add_handler # type: ignore
    logging.Logger.handle = audited_log_handle # type: ignore
    try:
        started = time.perf_counter()
        importlib.import_module(target)
        duration_ms = (time.perf_counter() - started) * 1000
    finally:
        threading.Thread.start = original_thread_start
        logging.Logger.addHandler = original_add_handler
        logging.Logger.handle = original_handle
    rss_delta_kib = max(0, _rss_kib() - rss_before)

    if threading.active_count() != threads_before:
        side_effect_events.append("thread-count")
    if tuple(logging.getLogger().handlers) != handlers_before:
        side_effect_events.append("root-logging-handler")

    optional_modules = sorted(
        prefix
        for prefix in OPTIONAL_MODULE_PREFIXES
        if any(
            name == prefix or name.startswith(f"{prefix}.")
            for name in sys.modules
        )
    )
    return {
        "duration_ms": duration_ms,
        "optional_modules": optional_modules,
        "rss_delta_kib": rss_delta_kib,
        "side_effect_events": sorted(set(side_effect_events)),
        "target": target,
    }


def _validate_target(target: str) -> str:
    if target != "unicorefw" and not target.startswith("unicorefw."):
        raise ImportBudgetError("targets must be unicorefw or its submodules")
    if not all(part.isidentifier() for part in target.split(".")):
        raise ImportBudgetError(f"invalid import target: {target!r}")
    return target


def _run_worker(target: str) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    project_root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.benchmark_imports",
            "--worker",
            target,
        ],
        capture_output=True,
        check=False,
        cwd=project_root,
        env=environment,
        text=True,
        timeout=WORKER_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        diagnostic = completed.stderr.strip()[:1000]
        raise ImportBudgetError(
            f"{target} worker failed with status {completed.returncode}: "
            f"{diagnostic or 'no diagnostic'}"
        )
    if len(completed.stdout.encode("utf-8")) > MAX_WORKER_OUTPUT_BYTES:
        raise ImportBudgetError(f"{target} worker output exceeded the safety limit")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ImportBudgetError(f"{target} worker returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise ImportBudgetError(f"{target} worker result must be an object")
    return result


def benchmark_import(
    target: str,
    *,
    runs: int,
    forbid_optional: bool = False,
    maximum_median_ms: float | None = None,
    maximum_median_rss_kib: float | None = None,
) -> dict[str, Any]:
    """Benchmark one target in isolated child processes."""
    target = _validate_target(target)
    if (
        isinstance(runs, bool)
        or not isinstance(runs, int)
        or not 1 <= runs <= MAX_RUNS
    ):
        raise ImportBudgetError(f"runs must be between 1 and {MAX_RUNS}")
    for value, label in (
        (maximum_median_ms, "maximum median milliseconds"),
        (maximum_median_rss_kib, "maximum median RSS KiB"),
    ):
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ImportBudgetError(f"{label} must be a finite non-negative number")

    results = [_run_worker(target) for _ in range(runs)]
    side_effects = sorted(
        {
            event
            for result in results
            for event in result.get("side_effect_events", ())
        }
    )
    optional_modules = sorted(
        {
            module
            for result in results
            for module in result.get("optional_modules", ())
        }
    )
    durations = [float(result["duration_ms"]) for result in results]
    rss_deltas = [float(result["rss_delta_kib"]) for result in results]
    summary = {
        "maximum_ms": max(durations),
        "median_ms": statistics.median(durations),
        "median_rss_kib": statistics.median(rss_deltas),
        "optional_modules": optional_modules,
        "runs": runs,
        "side_effect_events": side_effects,
        "target": target,
    }

    violations = []
    if side_effects:
        violations.append(f"import side effects detected: {', '.join(side_effects)}")
    if forbid_optional and optional_modules:
        violations.append(
            f"optional modules imported: {', '.join(optional_modules)}"
        )
    if (
        maximum_median_ms is not None
        and summary["median_ms"] > maximum_median_ms
    ):
        violations.append(
            f"median {summary['median_ms']:.3f} ms exceeds "
            f"{maximum_median_ms:.3f} ms"
        )
    if (
        maximum_median_rss_kib is not None
        and summary["median_rss_kib"] > maximum_median_rss_kib
    ):
        violations.append(
            f"median RSS delta {summary['median_rss_kib']:.0f} KiB exceeds "
            f"{maximum_median_rss_kib:.0f} KiB"
        )
    if violations:
        raise ImportBudgetError(f"{target}: {'; '.join(violations)}")
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*")
    parser.add_argument("--runs", type=int, default=7)
    parser.add_argument("--forbid-optional", action="store_true")
    parser.add_argument("--max-median-ms", type=float)
    parser.add_argument("--max-median-rss-kib", type=float)
    parser.add_argument("--worker", metavar="TARGET", help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.worker:
        try:
            target = _validate_target(args.worker)
            print(json.dumps(_worker_result(target), sort_keys=True))
        except (ImportBudgetError, ImportError) as exc:
            print(f"import benchmark worker failed: {exc}", file=sys.stderr)
            return 1
        return 0
    if not args.targets:
        print("import benchmark failed: at least one target is required", file=sys.stderr)
        return 1

    try:
        summaries = [
            benchmark_import(
                target,
                runs=args.runs,
                forbid_optional=args.forbid_optional,
                maximum_median_ms=args.max_median_ms,
                maximum_median_rss_kib=args.max_median_rss_kib,
            )
            for target in args.targets
        ]
    except (ImportBudgetError, subprocess.TimeoutExpired) as exc:
        print(f"import benchmark failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summaries, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
