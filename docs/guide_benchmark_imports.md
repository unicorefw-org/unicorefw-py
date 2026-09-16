# `benchmark_imports.py` guide

Source: [`scripts/benchmark_imports.py`](../scripts/benchmark_imports.py)

## Purpose

Use this script to measure import time and resident-memory growth in fresh child
processes. It also detects optional dependency loading and import-time side
effects such as file writes, network connections, subprocesses, database
connections, thread starts, and root logging changes.

The command can enforce latency, memory, and optional-import budgets for each
target.

## Requirements

- Run the command from the repository root.
- Pass `unicorefw` or an identifier-safe `unicorefw.<submodule>` target.
- Use Linux for `/proc/self/statm` RSS measurements. Other platforms use the
  available `resource` fallback and may report different semantics.
- Use the same host and interpreter when comparing measurements.

## Commands

Enforce the root import contract used by CI:

```bash
python3 scripts/benchmark_imports.py unicorefw \
  --runs 9 \
  --forbid-optional \
  --max-median-ms 100 \
  --max-median-rss-kib 10240
```

Record several public submodules without absolute budgets:

```bash
python3 scripts/benchmark_imports.py \
  unicorefw.array \
  unicorefw.core \
  unicorefw.string \
  --runs 5
```

## Options

| Option | Default | Contract |
|---|---:|---|
| `targets` | required | One or more `unicorefw` import paths. At least one target is required. |
| `--runs N` | `7` | Integer from 1 through 50. Each run uses a new child process. |
| `--forbid-optional` | off | Fail if a worker imports a tracked optional dependency. |
| `--max-median-ms VALUE` | unset | Finite, non-negative median import-time ceiling per target. |
| `--max-median-rss-kib VALUE` | unset | Finite, non-negative median RSS-growth ceiling per target. |

Tracked optional prefixes are `cryptography`, `openpyxl`, `pandas`, `psycopg2`,
`pymongo`, `pymysql`, `redis`, and `sqlalchemy`.

## Output and exit status

The script prints a JSON array after all targets pass. Each target object
contains:

- `target` and `runs`;
- `median_ms` and `maximum_ms`;
- `median_rss_kib`;
- `optional_modules`;
- `side_effect_events`.

Exit status `0` means all targets passed. Exit status `1` means a target was
invalid, a worker failed or timed out, a side effect appeared, an optional
module violated policy, or a budget failed. The command does not print partial
JSON when one target fails. Argparse uses status `2` for malformed options.

## Safety and operational notes

Each worker has a 30-second timeout. The parent rejects worker output above 64
KiB and caps runs at 50. Workers disable bytecode writes with
`PYTHONDONTWRITEBYTECODE=1`.

Audit hooks detect file writes, `os.system`, socket connections, SQLite
connections, and subprocess creation. Instrumented wrappers detect thread and
logging changes. The audit reports observed events; it does not sandbox the
imported module.

Apply `--forbid-optional` to the dependency-free root or core contract. A
submodule designed to load an optional backend may fail that policy by design.

## Troubleshooting

`worker failed with status ...` includes up to 1,000 characters from worker
standard error. Run the target with `python3 -I -c 'import unicorefw.<name>'` to
separate an import error from a budget failure.

An RSS value of zero can mean the platform lacks both supported measurement
sources. Use the pinned Linux runner for enforced memory budgets.

Side-effect failures list event names. Locate the import that starts the event;
raising the time or memory limit will not resolve a side-effect violation.

