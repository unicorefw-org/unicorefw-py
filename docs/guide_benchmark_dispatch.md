# `benchmark_dispatch.py` guide

Source: [`scripts/benchmark_dispatch.py`](../scripts/benchmark_dispatch.py)

## Purpose

Use this script to measure four UniCoreFW call paths: a direct utility call, a
`UniCoreFW` static call, a factory-static call through `_`, and a five-step
wrapper chain. Each sample reports elapsed nanoseconds per call.

Set `--max-median-ns` when CI or a controlled runner must enforce a budget.

## Requirements

- Run the command from the repository root.
- Use the same Python build and host configuration for comparisons.
- Regenerate the core registry before measuring dispatch changes:

```bash
python3 scripts/generate_core_registry.py --check
```

## Commands

Run all four scenarios with the defaults:

```bash
python3 scripts/benchmark_dispatch.py
```

Run the PERF-003 measurement shape:

```bash
python3 scripts/benchmark_dispatch.py --runs 7 --iterations 100000
```

Enforce a median budget for one scenario:

```bash
python3 scripts/benchmark_dispatch.py \
  --scenario static \
  --runs 9 \
  --iterations 200000 \
  --max-median-ns 250
```

## Options

| Option | Default | Contract |
|---|---:|---|
| `--runs N` | `7` | Integer from 1 through 25. |
| `--iterations N` | `100000` | Integer from 1 through 1,000,000 per run. |
| `--scenario NAME` | all | Repeat to select more than one scenario. Choices are `direct`, `static`, `factory_static`, and `five_step_chain`. |
| `--max-median-ns VALUE` | unset | Finite, non-negative ceiling applied to each selected scenario. |

Scenario mapping:

| Scenario | Operation |
|---|---|
| `direct` | `unicorefw.utils.identity(value)` |
| `static` | `UniCoreFW.identity(value)` |
| `factory_static` | `_.identity(value)` |
| `five_step_chain` | Five chained `identity()` calls followed by `value()` |

## Output and exit status

The script writes a JSON array. Each object includes the scenario, run count,
iterations per run, median nanoseconds per call, and maximum nanoseconds per
call.

Exit status `0` means all result checks and configured budgets passed. Exit
status `1` means a result changed, a programmatic input violated a bound, or a
median exceeded `--max-median-ns`. Argparse uses status `2` for malformed CLI
arguments.

The maximum budget applies to each scenario. A command that selects four
scenarios fails when any one median exceeds the ceiling.

## Safety and operational notes

The script caps runs and iterations. It runs operations in the current process,
calls `gc.collect()` before each sample, and checks the final result after each
iteration loop.

The `direct` scenario serves as a control for host noise. A large movement in
that control weakens conclusions about changes in the other call paths. Pin CPU
governor settings and use a stable runner for release decisions.

## Troubleshooting

`dispatch benchmark failed: <scenario> median ... exceeds ...` means the budget
failed. Compare the direct-call control and rerun on the same host before
changing the threshold.

An unexpected-result failure indicates a behavior regression rather than a
performance regression. Run `tests/test_core_dispatch.py` and
`tests/test_import_contract.py` first.

