# `benchmark_collections.py` guide

Source: [`scripts/benchmark_collections.py`](../scripts/benchmark_collections.py)

## Purpose

Use this script to measure representative collection workloads in
`unicorefw.array`. It covers hash-backed fast paths, equality fallbacks, set-like
operations, right-side scanning, and front insertion. The script validates each
result before it reports a timing.

This command records measurements. It does not enforce a latency threshold.

## Requirements

- Run the command from the repository root.
- Use the Python interpreter and checkout you want to measure.
- Close CPU-heavy programs and keep the power profile fixed when comparing runs.
- Record the Python version, operating system, CPU, and command with published
  results.

## Commands

Run all scenarios with the defaults:

```bash
python3 scripts/benchmark_collections.py
```

Run the CI-sized workload:

```bash
python3 scripts/benchmark_collections.py --runs 5 --size 4000
```

Measure selected scenarios:

```bash
python3 scripts/benchmark_collections.py \
  --runs 7 \
  --size 8000 \
  --scenario uniq_all_unique \
  --scenario intersection_overlap
```

## Options

| Option | Default | Contract |
|---|---:|---|
| `--runs N` | `5` | Integer from 1 through 25. Each scenario runs `N` times. |
| `--size N` | `4000` | Integer from 1 through 20,000. Scenario factories may derive a smaller or larger item count. |
| `--scenario NAME` | all | Select one scenario. Repeat the option to select more than one. Argparse rejects unknown names. |

Available scenarios:

| Scenario | Workload |
|---|---|
| `uniq_duplicate_heavy` | Repeated integers with at most 64 unique values. |
| `uniq_all_unique` | Unique integers on the hash-backed path. |
| `uniq_mixed_hashability` | Alternating integers and one-item lists. Uses about one quarter of `--size`. |
| `uniq_unhashable` | Unique one-item lists. Uses about one quarter of `--size`. |
| `uniq_custom_equality` | Hashable dataclass values with equality semantics. |
| `union_all_unique` | Two disjoint lists, each containing `--size` integers. |
| `intersection_overlap` | Two lists with a half-range overlap. |
| `xor_overlap` | Two lists with a half-range overlap. |
| `take_right_while` | A predicate that accepts the full list. |
| `unshift` | Inserts `--size` values before one existing item. |

## Output and exit status

The script writes a JSON array to standard output. Each object contains:

- `scenario`: scenario name;
- `items`: the item count processed by that scenario;
- `runs`: sample count;
- `median_ms`: median elapsed milliseconds;
- `maximum_ms`: slowest elapsed milliseconds.

Exit status `0` means each selected scenario returned the expected result. Exit
status `1` means validation failed or a programmatic caller supplied an invalid
run count, size, scenario, or duplicate scenario. Argparse uses status `2` for
invalid command-line syntax and unknown choices.

## Safety and operational notes

The script caps run count and input size to limit CPU and memory use. It calls
`gc.collect()` before each sample. It imports `unicorefw.array` from the current
checkout and does not compare against an installed release.

Treat nanosecond and millisecond differences from separate hosts as distinct
experiments. Use the same interpreter, workload, host state, and run count for a
before-and-after comparison.

## Troubleshooting

`collection benchmark failed: ... returned an unexpected result` means the
operation violated the fixture contract. Run that scenario alone and execute
its unit tests before trusting timing data.

Large variance often comes from CPU frequency changes, WSL filesystem load, or
other processes. Increase `--runs` within the limit and compare medians on the
same host.

