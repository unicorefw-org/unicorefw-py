# `benchmark_release.py` guide

Source: [`scripts/benchmark_release.py`](../scripts/benchmark_release.py)

## Purpose

Use this script to compare an installed `unicorefw` release with the current
checkout. It measures matching API cases in isolated workers and records
whether both targets return equivalent results.

The benchmark registry covers the public API by category. A case can be
benchmarked, skipped, missing, or failed. The report preserves those states so
an incomplete comparison cannot be mistaken for a performance result.

## Requirements

- Run the command from the repository root.
- Install the release to compare in the same Python environment used to run
  the command.
- Keep the checkout importable from the repository root.
- Use the same machine, interpreter, power policy, and background workload for
  comparable timing results.

List mode does not import the installed release or local package.

## Commands

List categories and registered cases:

```bash
python3 scripts/benchmark_release.py --list
```

Run a bounded comparison for selected categories:

```bash
python3 scripts/benchmark_release.py \
  --category array \
  --category string \
  --iterations 100 \
  --repeats 7
```

Benchmark one API:

```bash
python3 scripts/benchmark_release.py \
  --api identity \
  --iterations 100 \
  --repeats 7
```

Require complete release coverage and write the report:

```bash
python3 scripts/benchmark_release.py \
  --strict \
  --json build/benchmark-release.json
```

Create `build/` before using the last command.

## Options

| Option | Default | Contract |
|---|---:|---|
| `--category NAME` | all | Select a category. Repeat the option to select more than one. |
| `--api NAME` | all | Select one exact registered API case. It may be combined with `--category`; the API must belong to that category. |
| `--iterations N` | `100` | Positive number of calls per case inside each timed repeat. |
| `--repeats N` | `7` | Positive number of timed repeats per case. |
| `--strict` | off | Fail on release gaps, release failures, skips, or result mismatches in addition to normal accounting and local-failure validation. |
| `--json PATH` | unset | Write the merged report as JSON after the workers finish. The parent directory must exist. |
| `--list` | off | Print category counts and case names, then exit without importing either target. |
| `--verbose` | off | Include the summary section in the text report. |

Available categories are `array`, `crypto`, `database`, `function`, `object`,
`orm`, `security`, `string`, `template`, `type`, and `utility`. The registry is
the authority for exact case counts; use `--list` instead of copying a count
into automation.

## Output and exit status

The default text report identifies the API, category, installed-release result,
checkout result, and comparison. Add `--verbose` to include the summary. Timed
cases report median latency. The JSON report is unchanged.
The JSON report contains the same merged case data in machine-readable form.

Without `--strict`, exit status `0` means all selected cases were accounted for
and no local case failed. Release gaps, release failures, intentional local
skips, and normalized-result mismatches remain visible in the report but do
not alone fail the command. With `--strict`, any of those conditions returns
status `1`. Malformed arguments and worker-process failures produce a nonzero
status.

## Safety and operational notes

The installed-release worker removes the checkout from its import path and
rejects a release import that resolves into the repository. The local worker
adds the repository root explicitly. This prevents both sides from measuring
the same checkout by mistake.

This script does not cap `--iterations` or `--repeats`, and it does not impose
a worker timeout. Use reviewed, bounded values in CI. Start with the defaults
before increasing either option.

`--json` writes directly to the requested path after comparison. Use a
disposable output path or move the completed file into place in workflows that
require atomic publication.

The ORM cases are intentionally skipped pending the replacement ORM design.
Optional dependency import failures can also appear as skips where a case
defines that behavior.

This benchmark is for release/local compatibility and public API latency, not
algorithm-scaling claims. Its registry uses bounded, fixed-size fixtures, so
its per-call timings are not comparable to the large-input collection results
reported by `scripts/benchmark_collections.py`.

## Troubleshooting

If the release import resolves to the checkout, uninstall editable installs
and install the wheel under test into a clean virtual environment.

If strict mode reports missing APIs, verify the installed release version and
inspect `--list`. A missing registry case is different from a failed timing
case and should not be hidden by increasing the workload.

If a command appears stuck, terminate it and lower `--iterations` or
`--repeats`. The script has no internal worker deadline.
