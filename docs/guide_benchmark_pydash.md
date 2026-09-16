# `benchmark_pydash.py` guide

Source: [`scripts/benchmark_pydash.py`](../scripts/benchmark_pydash.py)

## Purpose

Use this script to compare the local `unicorefw` checkout with a supported
`pydash` installation. It runs a fixed set of semantically compatible cases in
isolated workers, measures both targets, and rejects result mismatches.

The compatible-case allowlist is deliberate. Changing the expected pydash
version does not silently expand that list.

## Requirements

- Run the command from the repository root.
- Install pydash in the same Python environment. The default contract expects
  pydash `8.0.6`.
- Keep the local checkout importable from the repository root.
- Use the same host and interpreter for repeatable timing comparisons.

Install the default baseline into an isolated environment with:

```bash
python3 -m pip install 'pydash==8.0.6'
```

## Commands

List the compatible cases without importing either target:

```bash
python3 scripts/benchmark_pydash.py --list
```

Run selected categories:

```bash
python3 scripts/benchmark_pydash.py \
  --category array \
  --category object \
  --iterations 100 \
  --repeats 7
```

Benchmark one compatible API:

```bash
python3 scripts/benchmark_pydash.py \
  --api map_ \
  --iterations 100 \
  --repeats 7
```

Write a successful comparison atomically:

```bash
python3 scripts/benchmark_pydash.py \
  --json build/benchmark-pydash.json
```

Create `build/` before using the last command.

## Options

| Option | Default | Contract |
|---|---:|---|
| `--category NAME` | all | Select one of `array`, `function`, `object`, `string`, `type`, or `utility`. Repeat to select more than one. |
| `--api NAME` | all | Select one exact compatible API case. It may be combined with `--category`; the API must belong to that category. |
| `--iterations N` | `100` | Calls per timed repeat, from 1 through 1,000,000. |
| `--repeats N` | `7` | Timed repeats per case, from 1 through 100. |
| `--worker-timeout SECONDS` | `300` | Per-worker deadline from 1 through 3,600 seconds. |
| `--expected-pydash-version VERSION` | `8.0.6` | Expected distribution and module version. The value must contain 1 through 128 visible characters. |
| `--json PATH` | unset | Atomically write JSON only after a fully successful comparison. The parent directory must exist. |
| `--list` | off | Print category counts and compatible case names without importing either target. |
| `--verbose` | off | Include the API inventory and summary sections in the text report. |

## Output and exit status

The default report includes target paths and versions, the version policy,
per-case measurements, and result comparisons. Add `--verbose` to include the
full API inventory and summary. JSON output is unchanged.

Exit status `0` requires every selected case to be accounted for and
benchmarked successfully, with matching results and no missing, skipped, or
failed cases. A target import error, version mismatch, timeout, invalid worker
response, case mismatch, or malformed argument returns a nonzero status. JSON
is not published after a failed comparison.

## Safety and operational notes

The pydash worker rejects an import that resolves into the repository. It also
requires the installed distribution version, imported module version, and
expected version to agree. The local worker imports the checkout explicitly.

Workers run in isolated processes. Each has a bounded deadline, diagnostic
tails are limited to 4 KiB, and timed-out POSIX worker process groups are
terminated. Workload and timeout options have hard upper limits.

Overriding `--expected-pydash-version` acknowledges a different installed
version but does not certify semantic compatibility. Review the fixed case
allowlist and results before treating that comparison as a supported baseline.

## Troubleshooting

For a version-policy failure, run:

```bash
python3 -c 'import importlib.metadata, pydash; print(importlib.metadata.version("pydash"), pydash.__version__)'
```

Both values must match `--expected-pydash-version`.

If pydash resolves inside the checkout, remove the shadowing module or run in
a clean virtual environment. If a worker times out, first reduce iterations or
selected categories. Increase the timeout only after confirming the case is
making progress.

Treat a result mismatch as a semantic compatibility finding. More repeats can
improve timing confidence but cannot repair different return values.
